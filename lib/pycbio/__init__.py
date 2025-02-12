# Copyright 2006-2025 Mark Diekhans
import traceback

class PycbioException(Exception):
    """Base class for Pycbio exceptions."""
    pass

class PycbioOptionalFeatureException(PycbioException):
    """Thrown to indicate an optional feature is missing"""
    def __init__(self, feature, reason):
        super(PycbioOptionalFeatureException, self).__init__(f"{feature} is disabled due to {reason}")
        self.feature = feature
        self.reason = reason


def pycbioExFormat(ex):
    """Format any type of exception into list of new-line terminated, handling
    PycbioException objects and saved stack traces"""
    return traceback.format_exception(type(ex), ex, ex.__traceback__)


def pycbioExPrint(ex, file=None):
    """Format any type of exception into to a file, handling
    PycbioException objects and saved stack traces"""
    return traceback.print_exception(type(ex), ex, ex.__traceback__, file=file)
