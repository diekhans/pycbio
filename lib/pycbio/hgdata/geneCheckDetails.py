# Copyright 2006-2012 Mark Diekhans
from past.builtins import cmp
from future.standard_library import install_aliases
install_aliases()
from pycbio.tsv import TsvTable, TsvReader
import sys


def strOrNone(val):
    "return None if val is zero length otherwise val"
    if len(val) == 0:
        return None
    else:
        return sys.intern(val)


# acc	problem	info	chr	chrStart	chrEnd
typeMap = {"acc": intern,
           "problem": intern,
           "info": strOrNone,
           "chr": intern,
           "chrStart": int,
           "chrEnd": int}


def cmpByLocation(gcd1, gcd2):
    d = cmp(gcd1.chr, gcd2.chr)
    if d == 0:
        d = cmp(gcd1.chrStart, gcd2.chrStart)
        if d == 0:
            d = cmp(gcd1.chrEnd, gcd2.chrEnd)
    return d


class GeneCheckDetailsReader(TsvReader):
    def __init__(self, fileName, isRdb=False):
        TsvReader.__init__(self, fileName, typeMap=typeMap, isRdb=isRdb)


class GeneCheckDetailsTbl(TsvTable):
    """Table of GeneCheckDetails objects loaded from a Tsv.    """

    def __init__(self, fileName, isRdb=False):
        TsvTable.__init__(self, fileName, typeMap=typeMap, isRdb=isRdb)
