import os
import shutil

from django.core.mail import send_mail
from django.core.exceptions import ImproperlyConfigured

import git

import fnmatch
from ftpsync.targets import FsTarget
from ftpsync.ftp_target import FtpTarget
from ftpsync.synchronizers import UploadSynchronizer
from ftpsync.targets import DirMetadata

from .models import Listeners


class CustomUploadSynchronizer(UploadSynchronizer):
    def _match(self, entry):
        default_omit = [".DS_Store",
                        ".git",
                        ".hg",
                        ".svn",
                        DirMetadata.META_FILE_NAME,
                        DirMetadata.LOCK_FILE_NAME,
                        ]

        name = entry.name
        if name == DirMetadata.META_FILE_NAME:
            return False

        if name in default_omit:
            return False
        ok = True
        if entry.is_file() and self.include_files:
            ok = False
            for pat in self.include_files:
                if fnmatch.fnmatch(name, pat):
                    ok = True
                    break
        if ok and self.omit:
            for pat in self.omit:
                if fnmatch.fnmatch(name, pat):
                    ok = False
                    break
        return ok


class BitBucketClient:
    def __init__(self, repository_slug, listener_uuid):
        temp_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
        listener = Listeners.objects.get(pk=listener_uuid)
        self.__repo_url = listener.repository_url
        self.__dir = os.path.join(temp_root_dir, repository_slug)
        self.__repo = git.Repo.init()

    def __del__(self):
        self.clear_temp()

    def clone_branch_to_temp(self, branch):
        try:
            self.__repo.clone_from(self.__repo_url, self.__dir, branch=branch)
        except Exception as e:
            self.clear_temp()
            print(e.args)
            raise ImproperlyConfigured()

    def clear_temp(self):
        shutil.rmtree(self.__dir)

    @property
    def temp_dir(self):
        return self.__dir


class FTPClient:
    __omit = ''

    def __init__(self, local_dir, ftp_path, ftp_host, username, password):
        self.__local = FsTarget(local_dir)
        self.__remote = FtpTarget(ftp_path, ftp_host, 21, username, password)

        git_ignore_path = os.path.join(local_dir, '.gitignore')
        if os.path.isfile(git_ignore_path):
            self.__omit = self.parse_git_ignore(git_ignore_path, local_dir)

    def parse_git_ignore(self, git_ignore_path, local_dir):
        with open(git_ignore_path, 'r') as git_ignore_file:
            lines = git_ignore_file.readlines()

        ignores = []
        for line in lines:
            path = line.strip()
            if path[0] != '#':
                ignores.append(line.strip())
        return ",".join(ignores)

    def push_files(self):
        opts = {"verbose": 3, "dry_run": False, 'omit': self.__omit, "delete_unmatched": True}
        synchronizer = CustomUploadSynchronizer(self.__local, self.__remote, opts)
        synchronizer.run()


class MailClient:
    def __init__(self):
        pass

    def send_email(self):
        pass
