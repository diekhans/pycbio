# Copyright 2006-2018 Mark Diekhans
"""
Special pretty printing stuff.
"""
import sys
from pprint import PrettyPrinter


class NoStrWrapPrettyPrinter(PrettyPrinter):
    """pretty printing without wrapping in the middle of strings"""
    # Martijn Pieters from https://stackoverflow.com/questions/31485402/can-i-make-pprint-in-python3-not-split-strings-like-in-python2
    def _format(self, object, *args):
        if isinstance(object, str):
            width = self._width
            self._width = sys.maxsize
            try:
                super(NoStrWrapPrettyPrinter, self)._format(object, *args)
            finally:
                self._width = width
        else:
            super(NoStrWrapPrettyPrinter, self)._format(object, *args)

def nswpprint(object, stream=None, indent=1, width=80, depth=None, compact=False):
    """Pretty-print a Python object to a stream [default is sys.stdout] without
    wrapping strings"""
    printer = NoStrWrapPrettyPrinter(stream=stream, indent=indent, width=width, depth=depth, compact=compact)
    printer.pprint(object)


__all__ = [nswpprint.__name__, NoStrWrapPrettyPrinter.__name__]
