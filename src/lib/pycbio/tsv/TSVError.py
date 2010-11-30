# Copyright 2006-2010 Mark Diekhans
from pycbio.sys import PycbioException

class TSVError(PycbioException):
    "Error from reading or parsing a TSV file"
    def __init__(self, msg, reader=None, cause=None):
        if (reader != None):
            msg = reader.fileName + ":" + str(reader.lineNum) + ": " + msg
        PycbioException.__init__(self, msg, cause)
