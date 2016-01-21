import os
import ftplib
import shutil

from django.core.exceptions import ImproperlyConfigured

import git

from .models import Listeners, Emails


class FtpSynchronizer():
    def __init__(self, ftp_host, ftp_port, ftp_user, ftp_pass, local_dir, remote_dir, omit):
        self.ftp_host = ftp_host
        self.ftp_port = ftp_port
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass
        self.local_dir = local_dir
        self.remote_dir = remote_dir
        self.connection = ftplib.FTP()
        self.omit = omit

    # Remove trailing slash
    def stripslashes(self, string):
        if string is "":
            return string
        if string[-1] is "/":
            return string[:-1]
        else:
            return string

    # Remove empty elements in array
    def remove_empty(self, array):
        count = 0
        for elem in array:
            if not elem:
                del array[count]
            count = count + 1
        return array

    # Connect to FTP server and login
    def connect(self):
        self.connection.connect(self.ftp_host, self.ftp_port)
        self.connection.login(self.ftp_user, self.ftp_pass)

    # Check if remote object is a directory
    def is_dir(self, dirname):
        current = self.connection.pwd()
        try:
            self.connection.cwd(dirname)
            is_dir = True
            self.connection.cwd(current)
        except Exception:
            is_dir = False

        return is_dir

    # Recursively delete remote directory
    def delete_dir(self, dirname):

        terminated = False

        def outer_delete_dir(outer_dirname):
            nonlocal terminated
            current = self.connection.pwd()
            try:
                self.connection.rmd(outer_dirname)
            except Exception:
                self.connection.cwd(outer_dirname)
                for elem in self.connection.mlsd():
                    if elem[0] in ('.', '..'):
                        continue

                    absolute_path = os.path.join(current, outer_dirname, elem[0])
                    if absolute_path in self.omit:
                        terminated = True
                        continue

                    try:
                        self.connection.delete(elem[0])
                    except Exception:
                        try:
                            self.connection.rmd(elem[0])
                        except Exception:
                            outer_delete_dir(elem[0])

                self.connection.cwd(current)
                if not terminated:
                    self.connection.rmd(outer_dirname)

        outer_delete_dir(dirname)

    # Upload local directory to remote
    def sync(self):
        self.connect()  # connect

        # navigate to remote destination
        remote_current = self.connection.pwd()

        dest_remote = self.remote_dir
        dest_remote = dest_remote.replace(remote_current, "", 1)
        dest_remote = self.stripslashes(dest_remote)
        self.connection.cwd(dest_remote)

        for case in os.walk(self.local_dir):
            path = case[0]  # absolute path
            dirs = case[1]  # directories in the directory
            files = case[2]  # files in the direcotry

            relative_path = self.stripslashes(path.replace(self.stripslashes(self.local_dir), "", 1))

            self.connection.cwd(self.remote_dir + relative_path)  # Change working directory to dir in os.walk

            for directory in dirs:
                try:
                    self.connection.mkd(directory)
                except Exception:
                    pass  # If directory exists, program will hit the error and not create new

            for f in files:
                try:
                    self.connection.delete(f)
                except Exception:
                    pass  # If file exists, program will delete it. Else hit error.

                # Upload file
                self.connection.storbinary("STOR " + f, open(path + "/" + f, "rb"))

            current = self.connection.pwd()

            for elem in self.connection.mlsd():
                # Elem is every dir+file on remote
                if elem[0] in ('.', '..'):
                    continue

                absolute_path = os.path.join(current, elem[0])
                if absolute_path in self.omit:
                    continue

                if self.is_dir(elem[0]) and (not elem[0] in dirs):  # If remote is dir, and not present on local
                    self.delete_dir(elem[0])
                elif (not self.is_dir(elem[0])) and (
                        not elem[0] in files):  # If remote is file, and not present on local
                    self.connection.delete(elem[0])


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


class FtpClient:
    __omit = ''

    def __init__(self, local_dir, ftp_path, ftp_host, username, password):
        self.__local_dir = local_dir
        self.__ftp_path = ftp_path
        self.__ftp_host = ftp_host
        self.__username = username
        self.__password = password

        git_ignore_path = os.path.join(local_dir, '.gitignore')
        if os.path.isfile(git_ignore_path):
            self.__omit = self.parse_git_ignore(git_ignore_path)

    def parse_git_ignore(self, git_ignore_path):
        with open(git_ignore_path, 'r') as git_ignore_file:
            lines = git_ignore_file.readlines()

        ignores = []
        for line in lines:
            path = line.strip()
            if path[0] != '#':
                ignores.append(self.__ftp_path + '/' + line.strip().lstrip('/'))
        return ignores

    def push_files(self):
        ftp_sync = FtpSynchronizer(self.__ftp_host, 21, self.__username, self.__password, self.__local_dir,
                                   self.__ftp_path, self.__omit)

        ftp_sync.sync()
