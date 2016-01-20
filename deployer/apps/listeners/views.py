import json

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .models import Listeners, Logs
from .utils import BitBucketClient, FtpClient, MailClient


@csrf_exempt
def handle_webhook(request, listener_uuid=None):
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        repository_slug = data['repository']
        listener = get_object_or_404(Listeners, pk=listener_uuid)

        if listener.repository_slug != repository_slug:
            raise Http404("There is not listener for {}".format(repository_slug))

        Logs.create_record(listener, 'Listener was activated for: {}'.format(repository_slug))

        # is that commit to branch?
        if data['push']['new']['type'] != "branch" or data['push']['new']['target']['type'] != "commit":
            raise Http404("This is not commit to branch")
        else:
            commit_branch = data['push']['new']['name']

        Logs.create_record(listener, 'Listener commit branch: {}'.format(commit_branch))

        if listener.development_branch == commit_branch:
            push_type = 'development'
        elif listener.production_branch == commit_branch:
            push_type = 'production'
        else:
            raise Http404("Branch is not configured properly")

        Logs.create_record(listener, 'Listener push type: {}'.format(push_type))

        # clone repository
        repo = BitBucketClient(listener.repository_slug, listener.listener_uuid)
        repo.clone_branch_to_temp(commit_branch)
        repo_dir = repo.temp_dir

        Logs.create_record(listener, 'The branch was cloned')

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
            raise Http404(e.args)
        finally:
            del repo

        Logs.create_record(listener, 'The branch "{}" of repository {} was pushed to {} FTP server'.format(
            commit_branch, repository_slug, push_server_name), True)

        # remove tmp repo
        Logs.create_record(listener, 'Temporary data was removed')

        return HttpResponse('Have a nice day :)')

    else:
        raise Http404("Error in request")
