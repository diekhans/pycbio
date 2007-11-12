"""Experiment running module"""

import sys,traceback,types
from pycbio.sys import typeOps

class ExRunException(Exception):
    "Exceptions thrown by exrun module derive from this object" 
    pass

class Verb(object):
    """Verbose tracing, bases on a set of flags.  The str() of
    any object passed to print routines with the following exceptions:
      traceback - stack is formatted
    """
    
    # flag values
    error = intern("error")     # output erors
    trace = intern("trace")     # basic tracing
    details = intern("details") # detailed tracing
    graph = intern("graph")     # dump graph at the start

    def __init__(self, flags=None, fh=sys.stderr):
        self.fh = fh
        self.flags = flags
        if self.flags == None:
            self.flags = set([Verb.error, Verb.trace])
        self.indent = 0

    def enabled(self, flag):
        """determine if tracing is enabled for the specified flag, flag can be
        either a single flag or sequence of flags"""
        if typeOps.isListLike(flag):
            for f in flag:
                if f in self.flags:
                    return True
            return False
        else:
            return (flag in self.flags)

    def _prIndent(self, msg):
        ind = ("%*s" % (2*self.indent, ""))
        self.fh.write(ind)
        for m in msg:
            if isinstance(m, types.TracebackType):
                self.fh.write(ind.join(traceback.format_tb(m)))
            else:
                self.fh.write(str(m))
        self.fh.write("\n")
        self.fh.flush()

    def prall(self, *msg):
        "unconditionally print a message with indentation"
        self._prIndent(msg)

    def pr(self, flag, *msg):
        "print a message with indentation if flag indicates enabled"
        if self.enabled(flag):
            self._prIndent(msg)

    def enter(self, flag=None, *msg):
        "increment indent count, first optionally output a trace message"
        if self.enabled(flag) and (len(msg) > 0):
            self._prIndent(msg)
        self.indent += 1

    def leave(self, flag=None, *msg):
        "decrement indent count, then optionally outputing a trace message "
        self.indent -= 1
        if self.enabled(flag) and (len(msg) > 0):
            self._prIndent(msg)

# make classes commonly used externally part of top module
from pycbio.exrun.Graph import Production, Rule
from pycbio.exrun.CmdRule import CmdRule, Cmd, OFileRef, IFileRef, FileIn, FileOut, File
from pycbio.exrun.ExRun import ExRun


__all__ = (ExRunException.__name__, Verb.__name__, Production.__name__,
           Rule.__name__, CmdRule.__name__, Cmd.__name__, 
           "OFileRef", "IFileRef", File.__name__,
           FileIn.__name__, FileOut.__name__, ExRun.__name__)
