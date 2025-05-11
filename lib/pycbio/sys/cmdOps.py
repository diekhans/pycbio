# Copyright 2006-2025 Mark Diekhans
"""Miscellaneous command line parsing operations"""
import logging
from pycbio import NoStackError, exceptionFormat
from pycbio.sys.objDict import ObjDict

def getOptionalArgs(parser, args):
    """Get the parse command line option arguments (-- or - options) as an
    object were the options are fields in the object.  Useful for packaging up
    a large number of options to pass around."""

    opts = ObjDict()
    for act in parser._actions:
        if (len(act.option_strings) > 0) and (act.dest != 'help'):
            setattr(opts, act.dest, getattr(args, act.dest))
    return opts

def parse(parser):
    """call argparse parse_args and return (opts, args)"""
    args = parser.parse_args()
    return getOptionalArgs(parser, args), args

class ErrorHandler:
    """Command line error handling. This is a context manager that wraps execution
    of a program.  This is called after command line parsing has been done.
    If an exception is caught, it handles printing the error via logging, normally
    to stderr, and exits non-zero.

    If DEBUG log level is set, the call stack traceback will always be
    logged.  Otherwise, the stack is not print if the Exception inherits from
    NoStackError, or its class is in the noStackExcepts, or printStackFilter
    indicates is should not be printed.

    logger - use this logger if specified, otherwise the default logger.
    noStackExcepts  - if not None, exceptions classes to not print, defaults to (OSError, ImportError).
    printStackFilter - a function that is called with the exception object. If it returns
    True, the stack is printed, False it is not printed, and None, it defers to the noStackExcepts
    checks.

    Example:
        def main():
           opts, args = cmd_line_parse()
           with cmdOps.ErrorHandler():
              real_prog(opts, args.one, args.two)

    """
    DEFAULT_NO_STACK_EXCEPTS = (OSError, ImportError)

    def __init__(self, *, logger=None, noStackExcepts=DEFAULT_NO_STACK_EXCEPTS, printStackFilter=None):
        self.logger = logger if logger is not None else logging.getLogger()
        self.noStackExcepts = tuple(noStackExcepts) if noStackExcepts is not None else None
        self.printStackFilter = printStackFilter

    def __enter__(self):
        pass

    def _handleNoStackTrace(self, logger, exc_val):
        logger.error(exceptionFormat(showTraceback=False))

    def _handleStackTrace(self, logger, exc_val, exc_tb):
        logger.error(exceptionFormat(showTraceback=True))

    def _showTraceBack(self, exc_val):
        if self.logger.getEffectiveLevel() <= logging.DEBUG:
            return True
        if self.printStackFilter is not None:
            filt = self.printStackFilter(exc_val)
            if filt is not None:
                return filt
        if isinstance(exc_val, NoStackError):
            return False
        if self.noStackExcepts is None:
            return True
        return not isinstance(exc_val, self.noStackExcepts)

    def _handleError(self, exc_val):
        msg = exceptionFormat(exc_val, showTraceback=self._showTraceBack(exc_val))
        self.logger.error(msg.rstrip('\n'))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._handleError(exc_val)
            exit(1)
