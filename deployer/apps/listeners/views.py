import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import Listeners, Logs
from .utils import BitBucketClient, FtpClient, MailClient


def add_log_record(message='', listener=None, report=False):
    if listener is not None:
        Logs.create_record(listener, message, report)
    return message


@csrf_exempt
def handle_webhook(request, listener_uuid=None):
    if request.method == 'POST':

        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            return HttpResponseBadRequest("Cannot parse JSON data: {}".format(e.args))

        repository_slug = data['repository']

        try:
            listener = Listeners.objects.get(pk=listener_uuid)
            add_log_record(">>> Listener started for {}".format(listener.repository_slug), listener)
        except Listeners.DoesNotExist:
            return HttpResponseBadRequest('Wrong UUID')

        if listener.repository_slug != repository_slug:
            return HttpResponseBadRequest(
                add_log_record("!!! There is not listener for {}".format(repository_slug), listener, True))

        # is that commit to branch?
        if data['push']['new']['type'] != "branch" or data['push']['new']['target']['type'] != "commit":
            return HttpResponseBadRequest(add_log_record("!!! This is not commit to branch", listener, True))
        else:
            commit_branch = data['push']['new']['name']

        if listener.development_branch == commit_branch:
            push_type = 'development'
        elif listener.production_branch == commit_branch:
            push_type = 'production'
        else:
            return HttpResponseBadRequest(add_log_record("!!! Branch is not configured properly", listener, True))

        # clone repository
        repo = BitBucketClient(listener.repository_slug, listener.listener_uuid)
        try:
            repo.clone_branch_to_temp(commit_branch)
            repo_dir = repo.temp_dir
        except Exception as e:
            return HttpResponseBadRequest(add_log_record("!!! Cloning runtime error: {}".format(e.args), listener, True))

        add_log_record("Cloned branch <{}>".format(commit_branch), listener)

        # push new files to ftp server
        ftp_client, push_server_name = None, None
        if push_type == 'development':
            ftp_client = FtpClient(repo_dir, listener.development_server_path, listener.development_server.host,
                                   listener.development_server.username, listener.development_server.password)
            push_server_name = listener.development_server.name
        elif push_type == 'production':
            ftp_client = FtpClient(repo_dir, listener.production_server_path, listener.production_server.host,
                                   listener.production_server.username, listener.production_server.password)
            push_server_name = listener.production_server.name

        try:
            ftp_client.push_files()
        except Exception as e:
            return HttpResponseBadRequest(
                add_log_record("!!! FTP sync ({}) runtime error: {}".format(push_server_name, e.args), listener, True))
        finally:
            del repo

        add_log_record("Pushed to <{}>".format(push_server_name), listener)
        add_log_record(">>> Listener finished for {}".format(listener.repository_slug), listener)

        return HttpResponse('Have a nice day :)')

    else:
        return HttpResponseBadRequest("This is not a POST request")
