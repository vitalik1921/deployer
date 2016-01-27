import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import Listeners, Logs
from .utils import BitBucketClient, FtpClient, postpone


def add_log_record(message='', listener=None, report=False):
    if listener is not None:
        Logs.create_record(listener, message, report)
    return message


@postpone
def pull_and_push(listener, push_types):
    for push_type in push_types:
        if push_type == 'development':
            branch = listener.development_branch
            server = listener.development_server
            server_path = listener.development_server_path
        elif push_type == 'production':
            branch = listener.production_branch
            server = listener.production_server
            server_path = listener.production_server_path

        add_log_record("[BEGIN] Task execution was started for <{}>".format(listener.repository_slug), listener)

        # clone repository
        try:
            repo = BitBucketClient(listener.repository_slug, listener.listener_uuid)
            repo.clone_branch_to_temp(branch)
            repo_dir = repo.temp_dir
        except Exception as e:
            return HttpResponseBadRequest(
                add_log_record("[ !!! ] Cloning runtime error: {}".format(e.args), listener, True))

        add_log_record("[  *  ] Cloned branch <{}>".format(branch), listener)

        # push new files to ftp server
        ftp_client = FtpClient(repo_dir, server_path, server.host, server.username, server.password)
        try:
            ftp_client.push_files()
        except Exception as e:
            return HttpResponseBadRequest(
                add_log_record("[ !!! ] FTP sync ({}) runtime error: {}".format(server.name, e.args), listener, True))
        finally:
            del repo

        add_log_record("[  *  ] Repository <{}> with branch <{}> was pushed to <{}> successfully"
                       .format(listener.repository_slug, branch, server.name), listener)

        add_log_record("[ END ] Task execution was ended for <{}>".format(listener.repository_slug), listener, True)


@csrf_exempt
def handle_webhook(request, listener_uuid=None):
    if request.method == 'POST':

        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            return HttpResponseBadRequest("[ !!! ] Cannot parse JSON data: {}".format(e.args))

        try:
            repository_slug = data['repository']['name']
        except Exception as e:
            return HttpResponseBadRequest('[ !!! ] Request is not properly configured : {}'.format(e.args))

        try:
            listener = Listeners.objects.get(pk=listener_uuid)
        except Listeners.DoesNotExist:
            return HttpResponseBadRequest('[ !!! ] Wrong UUID')

        if listener.repository_slug != repository_slug:
            return HttpResponseBadRequest(
                add_log_record("[ !!! ] There is not listener for {}".format(repository_slug), listener, True))

        # what is the changes?
        changes = data['push']['changes']
        branches = []
        for change in changes:
            if change['new']['type'] == 'branch':
                branches.append(change['new']['name'])

        push_types = []
        if listener.development_branch in branches and listener.enable_development:
            push_types.append('development')
        if listener.production_branch in branches and listener.enable_production:
            push_types.append('production')

        if len(push_types) == 0:
            return HttpResponseBadRequest(
                add_log_record("[  !  ] There is no changes for development or production branches", listener, True))

        pull_and_push(listener, push_types)
        return HttpResponse('Have a nice day :)')

    else:
        return HttpResponseBadRequest("[ !!! ] This is not a POST request")


@csrf_exempt
def force_push(request, listener_uuid=None, push_type=None):
    if request.method == 'GET':

        try:
            listener = Listeners.objects.get(pk=listener_uuid)
        except Listeners.DoesNotExist:
            return HttpResponseBadRequest('[ !!! ] Wrong UUID')

        # what is the changes?
        push_types = []
        if push_type == 'development':
            push_types.append('development')

        if push_type == 'production':
            push_types.append('production')

        pull_and_push(listener, push_types)
        return HttpResponse('Task was scheduled')

    else:
        return HttpResponseBadRequest("[ !!! ] This is not a GET request")
