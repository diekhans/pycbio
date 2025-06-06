# Copyright 2006-2025 Mark Diekhans
import os
import errno
import socket
import fcntl
from pycbio import PycbioException


class _Fifo:
    """Object wrapper for pipes, abstracting traditional and named pipes,
    and hiding OS differences"""
    __slots__ = ("rfd", "wfd", "rfh", "wfh", "rpath", "wpath")

    def __init__(self):
        self.rfh = self.wfh = None

    def __del__(self):
        "finalizer"
        try:
            self.close()
        except Exception:
            pass

    def getRfh(self):
        "get read file object"
        if self.rfh is None:
            self.rfh = os.fdopen(self.rfd)
        return self.rfh

    def getWfh(self):
        "get write file object"
        if self.wfh is None:
            self.wfh = os.fdopen(self.wfd, "w")
        return self.wfh

    def rclose(self):
        "close read side if open"
        if self.rfd is not None:
            if self.rfh is not None:
                self.rfh.close()
            else:
                os.close(self.rfd)
            self.rfd = self.rfh = None

    def wclose(self):
        "close write side, if open"
        if self.wfd is not None:
            if self.wfh is not None:
                self.wfh.close()
            else:
                os.close(self.wfd)
            self.wfd = self.wfh = None

    def close(self):
        "close if open"
        # do write side first to ensure EOF if in single process
        if self.wfd is not None:
            self.wclose()
        if self.rfd is not None:
            self.rclose()


class _LinuxFifo(_Fifo):
    """Linus FIFO, that used /proc to get file paths"""

    def __init__(self):
        super(_LinuxFifo, self).__init__()
        self.rfd, self.wfd = os.pipe()
        # must do before forking, since path contains pid!
        self.rpath = _LinuxFifo._mkFdPath(self.rfd)
        self.wpath = _LinuxFifo._mkFdPath(self.wfd)

    @staticmethod
    def _mkFdPath(fd):
        "get linux /proc path for an fd"
        assert fd is not None
        p = "/proc/" + str(os.getpid()) + "/fd/" + str(fd)
        if not os.path.exists(p):
            raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), p)
        return p


class _NamedFifo(_Fifo):
    """FIFO, that used named pipes to get file paths"""

    def __init__(self):
        super(_NamedFifo, self).__init__()
        self.rpath = self.wpath = _NamedFifo._fifoMk()
        self.rfd = _NamedFifo._fifoOpen(self.rpath, "r")
        self.wfd = _NamedFifo._fifoOpen(self.wpath, "w")

    @staticmethod
    def _fifoOpen(path, mode):
        "open a FIFO file descriptor without blocking during open"
        # FIXME: O_NONBLOCK not right for write, maybe just drop this
        omode = os.O_RDONLY if (mode.startswith("r")) else os.O_WRONLY
        fd = os.open(path, omode | os.O_NONBLOCK)
        try:
            fcntl.fcntl(fd, fcntl.F_SETFL, omode)  # clear O_NONBLOCK
        except Exception:
            try:
                os.close(fd)
            finally:
                pass
            raise
        return fd

    @staticmethod
    def _fifoMk(suffix="tmp", tmpDir=None):
        "create a FIFO with a unique name in tmp directory"
        # FIXME: don't need suffix/tmpDir, unless this made of part the Fifo API
        if tmpDir is None:
            tmpDir = os.getenv("TMPDIR", "/var/tmp")
        prefix = "{}/{}.{}".format(tmpDir, socket.gethostname(), os.getpid())
        maxTries = 1000
        unum = 0
        while unum < maxTries:
            path = "{}.{}.{}".format(prefix, unum, suffix)
            if _NamedFifo._fifoMkAtomic(path):
                return path
            unum += 1
        raise PycbioException("unable to create a unique FIFO name in the form \"{}.*.{} after {} tries".format(prefix, suffix, maxTries))

    @staticmethod
    def _checkFifo(path):
        """check that fifo matches expected types and perms, catch security hold
        were it could be replace with another file"""
        pass  # FIXME implement

    @staticmethod
    def _fifoMkAtomic(path):
        "atomic create of a fifo, return false some file exists (might not be fifo)"
        if os.path.exists(path):
            return False
        # atomic create
        try:
            os.mkfifo(path, 0o600)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                return False
            raise
        _NamedFifo._checkFifo(path)
        return True

    def close(self):
        "close if open"
        _Fifo.close(self)
        if self.rpath is not None:
            os.unlink(self.rpath)
            self.rpath = self.wpath = None


_fifoClass = None


def factory():
    "get a FIFO object of the correct type for this OS"
    global _fifoClass
    if _fifoClass is None:
        if os.path.exists("/proc/self/fd"):
            _fifoClass = _LinuxFifo
        else:
            _fifoClass = _NamedFifo
    return _fifoClass()
