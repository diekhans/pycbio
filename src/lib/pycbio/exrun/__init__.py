"""Experiment running module"""

import sys,traceback,types

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

    def __init__(self, verbFlags=None, fh=sys.stderr):
        self.fh = fh
        if verbFlags == None:
            self.flags = set([Verb.error, Verb.trace])
        self.indent = 0

    def enabled(self, flag):
        """determine if tracing is enabled for the specified flag, flag can be either a single flag or a set"""
        if isinstance(flag, set):
            return (flag and self.flags)
        else:
            return (flag in self.flags)

    def _prIndent(self, msg):
        self.fh.write(("%*s" % (2*self.indent, "")))
        for m in msg:
            # FIXME: this doesn't work anyway, as object changes; see CmdTrace
            if type(m) == types.TracebackType:
                self.fh.write(traceback.format_tb(m)[0])
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


##__all__ = (ExRunException.__name__)


