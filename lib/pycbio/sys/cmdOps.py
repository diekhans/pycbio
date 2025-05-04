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
    """Command error handling. This is a context manager that wraps execution
    of a program.  This should be called after command line parsing has
    been done.  It handles printing exceptions via the logger.  Stack traces
    are not printed if the Exception inherits from NoStackError unless
    DEBUG log level is set.

    def main():
       opts, args = cmd_line_parse()
       with cmdOps.ErrorHandler():
          real_prog(opts, args.one, args.two)

    noStackExcepts  - if specified, these are list of addition exceptions beyond NoStackError

    """
    DEFAULT_NO_STACK_EXCEPTS = (NoStackError,)

    def __init__(self, *, logger=None, noStackExcepts=None):
        self.logger = logger
        if noStackExcepts is None:
            self.noStackExcepts = self.DEFAULT_NO_STACK_EXCEPTS
        else:
            self.noStackExcepts = self.DEFAULT_NO_STACK_EXCEPTS + tuple(noStackExcepts)

    def __enter__(self):
        pass

    def _handleNoStackTrace(self, logger, exc_val):
        logger.error(exceptionFormat(showTraceback=False))

    def _handleStackTrace(self, logger, exc_val, exc_tb):
        logger.error(exceptionFormat(showTraceback=True))

    def _handleError(self, exc_val):
        logger = self.logger if self.logger is not None else logging.getLogger()
        showTraceback = (not isinstance(exc_val, self.noStackExcepts)) or (logger.getEffectiveLevel() <= logging.DEBUG)
        msg = exceptionFormat(exc_val, showTraceback=showTraceback)
        logger.error(msg.rstrip('\n'))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._handleError(exc_val)
            exit(1)
