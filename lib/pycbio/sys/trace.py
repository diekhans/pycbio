# Copyright 2006-2012 Mark Diekhans
"""Debug tracing and stack dumps on signals """
# ideas from:
#  http://www.dalkescientific.com/writings/diary/archive/2005/04/20/tracing_python_code.html
import sys
import os
import types
import linecache
import threading
import signal
import traceback
from datetime import datetime

# FIXME: can this be replace by the pdb trace facility???.
# FIXME: can this be a context too.
# FIXME: allow file-like as well as file
# FIXME: should ignore traceback,linecache by default

# used to detect traces that are currently open to prevent closing
_activeTraceFds = set()


def getActiveTraceFds():
    "return snapshot of currently active traces"
    return frozenset(_activeTraceFds)


class Trace(object):
    """Trace object, associate with an open trace file.  File is flushed after
    each write to debug blocking"""

    def __init__(self, traceFileSpec, ignoreMods=None, inclThread=False, inclPid=False, callIndent=True):
        "open log file. ignoreMods is a sequence of module objects or names to skip"
        self._wasOpen = hasattr(traceFileSpec, "fileno")
        if self._wasOpen:
            self.fh = traceFileSpec
        else:
            self.fh = open(traceFileSpec, "w")
        _activeTraceFds.add(self.fh.fileno())
        self.inclThread = inclThread
        self.inclPid = inclPid
        self.callIndent = callIndent
        self.depth = 0
        self.ignoreMods = set()
        if ignoreMods is not None:
            for m in ignoreMods:
                if isinstance(m, types.ModuleType):
                    m = m.__name__
                self.ignoreMods.add(m)

    def enable(self):
        """enable logging on all threads. """
        assert(self.fh is not None)
        sys.settrace(self._callback)
        threading.settrace(self._callback)

    def disable(self):
        """disable logging on all threads."""
        sys.settrace(None)
        threading.settrace(None)

    def close(self):
        "disable and close log file"
        if self.fh is not None:
            self.disable()
            _activeTraceFds.remove(self.fh.fileno())
            if self._wasOpen:
                self.fh.close()
            self.fh = None

    def log(self, *args):
        """log arguments as a message followed by a newline"""
        # build string and output, as this minimize interleaved messages
        # discard output on I/O errors
        try:
            msg = []
            if self.inclPid:
                msg.append(str(os.getpid()))
                msg.append(": ")
            if self.inclThread:
                # can only include id, getting name will cause deadlock
                msg.append(str(threading._get_ident()))
                msg.append(": ")
            for a in args:
                msg.append(str(a))
            msg.append("\n")
            self.fh.write("".join(msg))
            self.fh.flush()
        except IOError:
            pass

    _indentStrs = {}  # cache of spaces for identation, indexed by depth

    def _getIndent(self):
        "get indentation string"
        if not self.callIndent:
            return ""
        i = Trace._indentStrs.get(self.depth)
        if i is None:
            i = Trace._indentStrs[self.depth] = "".ljust(4 * self.depth)
        return i

    def _logLine(self, frame, event):
        "log a code line"
        lineno = frame.f_lineno
        fname = frame.f_globals.get("__file__")
        if fname is not None:
            if (fname.endswith(".pyc") or fname.endswith(".pyo")):
                fname = fname[:-1]
            line = linecache.getline(fname, lineno)
        else:
            line = "<file name not available>"
        name = frame.f_globals["__name__"]
        self.log(name, ":", lineno, self._getIndent(), line.rstrip())

    _logEvents = frozenset(["call", "line"])

    def _callback(self, frame, event, arg):
        "trace event callback"
        if frame.f_globals["__name__"] not in self.ignoreMods:
            if event == "call":
                self.depth += 1
            elif event == "return":
                self.depth -= 1
                if self.depth < 0:
                    self.depth = 0
            # FIXME: not sure how Trace ended up None in python 2
            if (Trace is not None) and event in Trace._logEvents:
                self._logLine(frame, event)
        return self._callback

def _dumpStacksHandler(signal, frame):
    """Signal handler to print the stacks of all threads to stderr"""
    fh = sys.stderr
    print("###### stack traces {} ######".format(datetime.now().isoformat()), file=fh)
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    for threadId, stack in sys._current_frames().items():
        print("# Thread: {}({})".format(id2name.get(threadId, ""), threadId), file=fh)
        traceback.print_stack(f=stack, file=fh)
    print("\n", file=fh)
    fh.flush()

def enableDumpStack(sig=signal.SIGUSR1):
    """enable dumping stacks when the specified signal is received"""
    signal.signal(sig, _dumpStacksHandler)


__all__ = (getActiveTraceFds.__name__, Trace.__name__, enableDumpStack.__name__)
