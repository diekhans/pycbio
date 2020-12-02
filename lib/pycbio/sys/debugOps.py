# Copyright 2006-2012 Mark Diekhans
"""Functions useful for debugging"""
import os.path
import sys
import posix


def lsOpen(msg=None, file=sys.stderr, pid=None):
    """list open files, mostly for debugging"""
    if msg is not None:
        print(msg, file=file)
    if pid is None:
        pid = os.getpid()
    fddir = "/proc/" + str(pid) + "/fd/"
    fds = posix.listdir(fddir)
    fds.sort()
    for fd in fds:
        # entry will be gone for fd dir when it was opened
        fdp = fddir + fd
        if os.path.exists(fdp):
            print("   ", fd, " -> ", os.readlink(fdp), file=file)


__all__ = [lsOpen.__name__]
