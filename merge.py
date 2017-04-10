import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("merge-bzr-git")


    @property
    def bzr_dir(self):
        return self._args.bzr_dir

    @property
    def git_dir(self):
        return self._args.git_dir

    @property
    def revision(self):
        return int(self._args.start_revision)

            logger.error("No such directory: '{bzr_dir}'".format(bzr_dir=self._args.bzr_dir))
            logger.error("No such directory: '{git_dir}'".format(git_dir=self._args.git_dir))
class CommitOutOfRangeException(Exception):
    def __init__(self, revision):
        super(self).__init__("Revision '{revision_id}' is not a valid commit in this repository".format(revision_id=revision))
        self.revision = revision


        logger.debug("fetching diff...")

        logger.debug("parsing log...")

            if bzr_log.returncode == 3:
                raise CommitOutOfRangeException(revision)
        logger.debug("applying patch...")

        logger.debug("adding all files to current commit...")

        logger.debug("committing...")


        with open(os.devnull, 'w') as fp:
            if subprocess.Popen(shlex.split('git commit --message="{message}" --author="{author}" --date="{date}"'.format(
                                            author=author, date=timestamp, message=message)), env=environ, stdout=fp).wait() != 0:
                raise Exception("unexpected exit code from git during commit")
            logger.error("Failed to find bzr binary on this system.")
            logger.error("Failed to find git binary on this system.")
    with CurrentWorkingDirectory(args.bzr_dir):
        try:
            revision = args.revision
            while True:
                logger.debug("revision: {revision_id}".format(revision_id=revision))

                bzr = BzrCommit(revision)
                with CurrentWorkingDirectory(args.git_dir):
                    git = GitCommit()
                    git.apply(bzr.diff)
                    git.add_all_files()
                    git.commit(bzr.message, bzr.author, bzr.committer, bzr.timestamp)

                revision += 1

        except CommitOutOfRangeException as e:
            logger.info("Done! Final commit was:", e.revision-1)
            sys.exit(0)

        except Exception as e:
            logger.exception(e)