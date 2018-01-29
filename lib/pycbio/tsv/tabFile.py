# Copyright 2006-2012 Mark Diekhans

# FIXME: needed for faster readings, but needs cleaned up, need reader/writer
# classes
# FIXME add try and error msg with file/line num, move to row reader class; see fileOps.iterRows
import sys
import csv
from pycbio.sys import fileOps

csv.field_size_limit(sys.maxsize)


class TabFile(list):
    """Class for reading tab-separated files.
    """

    def __init__(self, fileName, rowClass=None, hashAreComments=False):
        """Read tab file into the object
        """
        self.fileName = fileName
        self.rowClass = rowClass
        for row in TabFileReader(self.fileName, rowClass=rowClass, hashAreComments=hashAreComments):
            self.append(row)


def TabFileReader(fspec, rowClass=None, hashAreComments=False, skipBlankLines=False):
    """generator over non-empty tab file rows"""
    def processLine(line):
        if hashAreComments and line.startswith("#"):
            return None
        row = line[0:-1].split('\t')
        if skipBlankLines and (len(row) == 0):
            return None
        return rowClass(row) if rowClass is not None else row

    lineNum = -1
    with fileOps.FileAccessor(fspec) as fh:
        for line in fh:
            lineNum += 1
            row = processLine(line)
            if row is not None:
                yield row
