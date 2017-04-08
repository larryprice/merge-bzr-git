#!/usr/bin/env python3

import argparse
import os
import shlex
import subprocess
import sys


class Arguments(object):
    def __init__(self, args):
        self._parse(args)

    def _parse(self, args):
        parser = argparse.ArgumentParser(description="Merge bazaar revisions into git repository using diffs")
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
