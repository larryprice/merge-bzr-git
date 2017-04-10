#!/usr/bin/env python3

import argparse
import contextlib
import os
import re
import shlex
import subprocess
import sys


class Arguments(object):
    def __init__(self, args):
        self._parse(args)

    def _parse(self, args):
        parser = argparse.ArgumentParser(description='Merge bazaar revisions into git repository using diffs')
        parser.add_argument('-b', '--bzr-dir', required=True,
                            help='Location of local bazaar repository')
        parser.add_argument('-g', '--git-dir', required=True,
                            help='Location of local git repository')
        parser.add_argument('-r', '--start-revision', default=1,
                            help='Initial bazaar revision (default: 1)')

        self._args = parser.parse_args()

    def validate(self):
        if not os.path.exists(self._args.bzr_dir):
            print("No such directory: '{bzr_dir}'".format(bzr_dir=self._args.bzr_dir))
            sys.exit(1)

        if not os.path.exists(self._args.git_dir):
            print("No such directory: '{git_dir}'".format(git_dir=self._args.git_dir))
            sys.exit(1)


class CurrentWorkingDirectory(contextlib.ExitStack):
    def __init__(self, newcwd):
        super().__init__()
        cwd = os.getcwd()
        os.chdir(newcwd)
        self.callback(lambda: os.chdir(cwd))


class BzrCommit(object):
    # Assumes correct working directory
    def __init__(self, revision):
        self.author = ''
        self.committer = {'name': '', 'email': ''}
        self.timestamp = ''
        self.message = ''

        self._fetch_diff(revision)
        self._parse_log(revision)

    def _fetch_diff(self, revision):
        bzr_diff = subprocess.Popen(shlex.split('bzr diff -c{} --format git'.format(revision)), stdout=subprocess.PIPE)
        out, err = bzr_diff.communicate()
        if bzr_diff.returncode != 1:
            raise Exception("unexpected exit code from bzr during diff")

        self.diff = ''
        regex = re.compile('diff --git /dev/null b/(.*)')
        created_file = True
        for line in out.decode('utf-8').split('\n'):
            match = regex.match(line)
            if match is not None:
                self.diff += line.replace('/dev/null', 'a/{capture}'.format(capture=match.groups(1)[0])) + '\n'
            elif created_file:
                self.diff += line.replace('new mode', 'new file mode') + '\n'
            else:
                self.diff += line + '\n'

    def _parse_log(self, revision):
        bzr_log = subprocess.Popen(shlex.split('bzr log -r {revision}'.format(revision=revision)), stdout=subprocess.PIPE)
        out, err = bzr_log.communicate()
        if bzr_log.returncode != 0:
            raise Exception("unexpected exit code from bzr during log")

        recording_message = False
        for line in out.decode('utf-8').split('\n'):
            if recording_message:
                if line.startswith('  '):
                    self.message += line.strip() + '\n'
                    continue
                else:
                    recording_message = False

            if line.startswith("author: "):
                self.author = line.lstrip("author: ")
            elif line.startswith("committer: "):
                committer = re.match("committer: ([^<>]+) <(.+)>", line)
                if committer and len(committer.groups()) == 2:
                    self.committer = {'name': committer.groups()[0], 'email': committer.groups()[1]}
            elif line.startswith("timestamp: "):
                self.timestamp = line.lstrip("timestamp: ")
            elif line.startswith("message:"):
                recording_message = True


class GitCommit(object):
    # Assumes correct working directory
    def __init__(self):
        pass

    def apply(self, diff_data):
        git_patch = subprocess.Popen(shlex.split('git apply'), stdin=subprocess.PIPE)
        git_patch.communicate(input=diff_data.encode('utf-8'))
        if git_patch.returncode != 0:
            raise Exception("unexpected exit code from git during apply")

    def add_all_files(self):
        if subprocess.Popen(shlex.split('git add .')).wait() != 0:
            raise Exception("unexpected exit code from git during add")

    def commit(self, message, author, committer, timestamp):
        environ = os.environ.copy()
        environ['GIT_COMMITTER_NAME'] = committer['name']
        environ['GIT_COMMITTER_EMAIL'] = committer['email']
        environ['GIT_COMMITTER_DATE'] = timestamp
        if subprocess.Popen(shlex.split('git commit --message="{message}" --author="{author}" --date="{date}"'.format(
                                        author=author, date=timestamp, message=message)), env=environ).wait() != 0:
            raise Exception("unexpected exit code from git during commit")


if __name__ == '__main__':
    args = Arguments(sys.argv)
    args.validate()

    with open(os.devnull, 'w') as fp:
        if subprocess.Popen(shlex.split('which bzr'), stdout=fp).wait() != 0:
            print("Failed to find bzr binary on this system.")
            sys.exit(2)

        if subprocess.Popen(shlex.split('which git'), stdout=fp).wait() != 0:
            print("Failed to find git binary on this system.")
            sys.exit(2)

    with CurrentWorkingDirectory(args._args.bzr_dir):
        bzr = BzrCommit(args._args.start_revision)
        with CurrentWorkingDirectory(args._args.git_dir):
            git = GitCommit()
            git.apply(bzr.diff)
            git.add_all_files()
            git.commit(bzr.message, bzr.author, bzr.committer, bzr.timestamp)
