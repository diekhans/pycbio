# Copyright 2006-2012 Mark Diekhans
from __future__ import print_function
import sys
import traceback

# FIXME: wanted to move this up a level, see doc/issues.org as why this didn't work


class PycbioException(Exception):
    """Base class for exceptions.  This implements exception chaining and
    stores a stack trace.

    To chain an exception
       try:
          ...
       except Exception as ex:
          raise PycbioException("more stuff", ex)
    """
    def __init__(self, msg, cause=None):
        """Constructor."""
        if (cause is not None) and (not isinstance(cause, PycbioException)):
            # store stack trace in other Exception types
            exi = sys.exc_info()
            if exi is not None:
                try:
                    setattr(cause, "stackTrace", traceback.format_list(traceback.extract_tb(exi[2])))
                except TypeError:
                    # FIXME: not the best way to handle
                    # TypeError: can't set attributes of built-in/extension type 'exceptions.IOError'
                    pass
        super(PycbioException, self).__init__(msg)
        self.cause = cause
        self.stackTrace = traceback.format_list(traceback.extract_stack())[0:-1]

    def __str__(self):
        "recursively construct message for chained exception"
        desc = super(PycbioException, self).__str__()
        if self.cause is not None:
            desc += ",\n    caused by: {}: {}".format(self.cause.__class__.__name__, self.cause)
        return desc

    def format(self):
        "Recursively format chained exceptions into a string with stack trace"
        return PycbioException.formatExcept(self)

    @staticmethod
    def formatExcept(ex, doneStacks=None):
        """Format any type of exception, handling PycbioException objects and
        stackTrace added to standard Exceptions."""
        desc = str(ex)
        st = getattr(ex, "stackTrace", None)
        if st is not None:
            if doneStacks is None:
                doneStacks = set()
            for s in st:
                if s not in doneStacks:
                    desc += s
                    doneStacks.add(s)
        ca = getattr(ex, "cause", None)
        if ca is not None:
            desc += "caused by: " + PycbioException.formatExcept(ca, doneStacks)
        return desc
