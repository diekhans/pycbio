# Copyright 2006-2012 Mark Diekhans
from pycbio.tsv import TsvTable, TsvReader
import sys


def strOrNone(val):
    "return None if val is zero length otherwise val"
    if len(val) == 0:
        return None
    else:
        return sys.intern(val)


# acc	problem	info	chr	chrStart	chrEnd
typeMap = {"info": strOrNone,
           "chrStart": int,
           "chrEnd": int}


def GeneCheckDetailsReader(fspec):
    for gc in TsvReader(fspec, typeMap=typeMap):
        yield gc


class GeneCheckDetailsTbl(TsvTable):
    """Table of GeneCheckDetails objects loaded from a Tsv.    """
    def __init__(self, fspec):
        TsvTable.__init__(self, fspec, typeMap=typeMap)
