# Copyright 2006-2025 Mark Diekhans
"""Support for command line parsing"""
#import argparse
from pycbio import argparse
import logging
import traceback
from functools import partial
from io import StringIO
from pycbio import NoStackError
from pycbio.sys.objDict import ObjDict
from pycbio.sys import loggingOps


def splitOptionsArgs(parser, inargs):
    """Split command line arguments into two objects one of option arguments
    (-- or - options) and one of positional arguments.  Useful for packaging up
    a large number of options to pass around.  This does not handle subparsers
    unless the subparsers is the supplied parser, not the top-level one used
    in parsing"""

    opts = ObjDict()
    args = ObjDict()
    optnames = set([a.dest for a in parser._actions if a.option_strings])
    for name, value in vars(inargs).items():
        if name in optnames:
            opts[name] = value
        else:
            args[name] = value
    return opts, args

def parseOptsArgs(parser, args=None, namespace=None):
    """Call argparse parse_args and return (opts, args)"""
    return splitOptionsArgs(parser, parser.parse_args(args=args, namespace=namespace))

class _SubparsersActionWrapper:
    """Used to pass through the pointer to the parent parser in ArgumentParserExtras"""
    def __init__(self, subparsers_action, parent):
        self._action = subparsers_action
        self._parent = parent

        # parser creation from action
        def factory(*args, **kwargs):
            return type(parent)(*args, parent=self._parent, **kwargs)
        self._action._parser_class = factory

    def add_parser(self, name, **kwargs):
        return self._action.add_parser(name, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._action, attr)

class ArgumentParserExtras(argparse.ArgumentParser):
    """Wrapper around ArgumentParser that adds logging
    related extra options.  Also can parse splitting options and positional
    arguments into separate objects.
    """

    ###
    # This is a bit tricky because of sub-parsers and uses too much
    # internal knowledge of argparse.
    #
    # Want to add the logging options to the top-level parent parser.  This is
    # done by adding pointer to the parent parser at in each object.  It
    # requires a wrapper for the action object returned by add_subparsers()
    # to pass though the parent information
    #
    # In order to be able to split options, we have to find the leaf
    # sub-parser to get all of option definitions
    #
    # This also intercepts the functions to parser arguments to enable
    # logging based on the logging arguments.
    ##

    def __init__(self, *args, parent=None, incl_syslog=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self._subparser_map = {}
        if parent is None:
            loggingOps.addCmdOptions(self, inclSyslog=incl_syslog)

    def _find_subparser_action(self):
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                return action
        return None

    def _find_parser_used(self, parsed_args):
        """Find the parser object used to parse the arguments.
        """
        parser = self

        # Traverse through the subparser hierarchy using parsed argument values
        while parser:
            subparsers_action = parser._find_subparser_action()
            if subparsers_action is None:
                break

            # Find the next command in parsed args
            cmd_name = getattr(parsed_args, subparsers_action.dest, None)
            if (cmd_name is None) or (cmd_name not in subparsers_action.choices):
                break
            parser = subparsers_action.choices[cmd_name]

        return parser

    def _enable_logging(self, parsed_args):
        loggingOps.setupFromCmd(parsed_args, prog=self.prog)

    def add_subparsers(self, **kwargs):
        # need to create new parser including parent to pass through
        parser_factory = partial(ArgumentParserExtras, parent=self)

        # save of _SubParsersAction object to find subparser use
        action = super().add_subparsers(**kwargs)
        self._subparsers_action = action
        return self._subparsers_action

    def parse_known_args(self, args=None, namespace=None):
        "wrapper around parse_known_args to setup logging"
        # parse_args() goes through this function

        parsed_args, argv = super().parse_known_args(args, namespace)
        self._enable_logging(parsed_args)
        return parsed_args, argv

    def parse_known_intermixed_args(self, args=None, namespace=None):
        "wrapper around parse_known_intermixed_args to setup logging"
        # parse_intermixed_args goes through this function

        parsed_args, argv = super().parse_known_intermixed_args(args, namespace)
        self._enable_logging(parsed_args)
        return parsed_args, argv

    def parse_opts_args(self, args=None, namespace=None):
        """Return the parse command line option arguments (-- or - arguments) as an
        object where the options are fields in the object.  Useful for packaging up
        a large number of options to pass around without the temptation to pass
        the positional args as well. Returns (opts, args).
        """
        parsed_args = self.parse_args(args, namespace)
        return splitOptionsArgs(self._find_parser_used(parsed_args), parsed_args)


def _exceptionPrintNoTraceback(exc, file, indent):
    depth = 0
    while exc:
        if depth > 0:
            prefix = depth * '  ' if indent else ''
            file.write(f"{prefix}Caused by: ")
        file.write(f"{type(exc).__name__}: {str(exc)}\n")
        exc = exc.__cause__ or exc.__context__
        depth += 1

def _exceptionPrint(exc, *, file=None, showTraceback=True, indent=True):
    """print a chained exception following causal chain"""
    if showTraceback:
        traceback.print_exception(exc, file=file)
    else:
        _exceptionPrintNoTraceback(exc, file, indent)

def _exceptionFormat(exc, *, showTraceback=True, indent=True):
    """format a chained exception following causal chain"""
    fh = StringIO()
    _exceptionPrint(exc, file=fh, showTraceback=showTraceback, indent=indent)
    return fh.getvalue()


class ErrorHandler:
    """Command line error handling. This is a context manager that wraps execution
    of a program.  This is called after command line parsing has been done.
    If an exception is caught, it handles printing the error via logging, normally
    to stderr, and exits non-zero.

    If DEBUG log level is set, the call stack traceback will always be logged.
    Otherwise, the stack is not print if the Exception inherits from
    NoStackError, or its class is in the noStackExcepts, or printStackFilter
    indicates is should not be printed.

    noStackExcepts  - if not None, exceptions classes to not print, defaults to (OSError, ImportError).
    printStackFilter - a function that is called with the exception object. If it returns
    True, the stack is printed, False it is not printed, and None, it defers to the noStackExcepts
    checks.

    Example:
        def main():
           opts, args = cmd_line_parse()
           with cli.ErrorHandler():
              real_prog(opts, args.one, args.two)

    """
    DEFAULT_NO_STACK_EXCEPTS = (OSError, ImportError)

    def __init__(self, *, noStackExcepts=DEFAULT_NO_STACK_EXCEPTS, printStackFilter=None):
        self.noStackExcepts = tuple(noStackExcepts) if noStackExcepts is not None else None
        self.printStackFilter = printStackFilter

    def __enter__(self):
        pass

    def _showTraceBack(self, logger, exc_val):
        if logger.getEffectiveLevel() <= logging.DEBUG:
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
        logger = logging.getLogger()
        showTraceback = self._showTraceBack(logger, exc_val)
        msg = _exceptionFormat(exc_val, showTraceback=showTraceback)
        if not showTraceback:
            msg += "Specify --log-debug for details"
        logger.error(msg.rstrip('\n'))

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if isinstance(exc_val, SystemExit):
                raise exc_val
            else:
                self._handleError(exc_val)
                exit(1)
