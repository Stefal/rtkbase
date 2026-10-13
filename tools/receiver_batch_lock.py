"""Nonblocking process-wide coordination using a shared, server-owned lock path."""
import errno
import os

class BatchBusy(RuntimeError):
    pass

class ReceiverBatchLock:
    def __init__(self, path, shared=False):
        self.path = os.fspath(path)
        self.shared = shared
        self.fd = None

    def __enter__(self):
        flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
        self.fd = os.open(self.path, flags, 0o600)
        try:
            if os.name == 'nt':
                import msvcrt
                # Windows byte-range locks also cover bytes beyond end of file.
                msvcrt.locking(self.fd, msvcrt.LK_NBRLCK if self.shared else msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, (fcntl.LOCK_SH if self.shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
        except OSError as error:
            os.close(self.fd)
            self.fd = None
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise BatchBusy('Another receiver configuration is running') from error
            raise
        return self

    def __exit__(self, *args):
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
            self.fd = None
        # Keep the lock file: unlinking would permit locks on different inodes.
