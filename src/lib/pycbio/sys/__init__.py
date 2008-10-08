import sys, traceback

class PycbioException(Exception):
    """Base class for exceptions.  This implements exception chaining and
    stores a stack trace.
    """
    def __init__(self, msg, cause=None):
        """Constructor."""
        if (cause != None) and (not isinstance(cause, PycbioException)):
            # store stack trace in other Exceptions
            exi = sys.exc_info()
            if exi != None:
                cause.__dict__["stackTrace"] = traceback.format_list(traceback.extract_tb(exi[2]))
        Exception.__init__(self, msg)
        self.cause = cause
        print traceback.format_list(traceback.extract_stack())
        self.stackTrace = traceback.extract_stack())[0:-1]

    def __str__(self):
        "recursively construct message for chained exception"
        desc = ""
        desc += self.message
        if self.cause != None:
            desc += ", caused by "
            if isinstance(self.cause, PycbioException):
                desc += str(self.cause)
            else:
                desc += self.cause.message
        return desc

    def format(self):
        "Recursively format chained exceptions into a string with stack trace"
        return PycbioException.formatExcept(self)

    @staticmethod
    def formatExcept(ex):
        """Format any type of exception, handling PycbioException objects and
        stackTrace added to standard Exceptions"""
        desc = ""
        desc += type(ex).__name__ + ": " + ex.message + "\n"
        st = getattr(ex, "stackTrace", None)
        if st != None:
            desc += st
        ca = getattr(ex, "cause", None)
        if ca != None:
            desc += "caused by: " + PycbioException.formatExcept(ca)
        return desc
