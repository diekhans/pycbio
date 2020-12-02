# Copyright 2006-2012 Mark Diekhans
import traceback

# FIXME: wanted to move this up a level, see doc/issues.org as why this didn't work


class PycbioException(Exception):
    """Base class for exceptions.
    """
    pass

def pycbioExFormat(ex):
    """Format any type of exception into list of new-line terminateds, handling
    PycbioException objects and saved stack traces"""
    return traceback.format_exception(type(ex), ex, ex.__traceback__)


def pycbioExPrint(ex, file=None):
    """Format any type of exception into to a file, handling
    PycbioException objects and saved stack traces"""
    return traceback.print_exception(type(ex), ex, ex.__traceback__, file=file)
