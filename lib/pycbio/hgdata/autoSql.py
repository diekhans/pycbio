# Copyright 2006-2026 Mark Diekhans
"""support classes for parsing autoSql generated objects"""

##
# string array
##
def strArraySplit(commaStr):
    "parser for comma-separated string list into a list"
    if len(commaStr) == 0:
        return []
    # autosql uses longblob, so if this came from a mysql database, we need to convert to bytes
    if isinstance(commaStr, bytes):
        commaStr = commaStr.decode('utf-8')
    strs = commaStr.split(",")
    if commaStr.endswith(","):
        strs = strs[0:-1]
    return strs


def strArrayJoin(strs):
    """formatter for a list of values into a comma separated string, not-str values are
    converted to a string"""
    if (strs is None) or (len(strs) == 0):
        return ""
    return ",".join([str(s) for s in strs]) + ","


# TSV typeMap tuple for str arrays
strArrayType = (strArraySplit, strArrayJoin)

##
# int arrays
##
def intArraySplit(commaStr):
    "parser for comma-separated string list into a list of ints"
    ints = []
    for s in strArraySplit(commaStr):
        ints.append(int(s))
    return ints


def intArrayJoin(ints):
    "formatter for a list of ints into a comma seperated string"
    if (ints is None) or (len(ints) == 0):
        return ""
    strs = []
    for i in ints:
        strs.append(str(i))
    return ",".join(strs) + ","


# TSV typeMap tuple for str arrays
intArrayType = (intArraySplit, intArrayJoin)

##
# float arrays
##
def floatArraySplit(commaStr):
    "parser for comma-separated string list into a list of floats"
    floats = []
    for s in strArraySplit(commaStr):
        floats.append(float(s))
    return floats


def floatArrayJoin(floats, fmt=None):
    "formatter for a list of floats a comma seperated string"
    if (floats is None) or (len(floats) == 0):
        return ""
    strs = []
    for f in floats:
        strs.append(fmt.format(f) if fmt is not None else str(f))
    return ",".join(strs) + ","


# TSV typeMap tuple for str arrays
floatArrayType = (floatArraySplit, floatArrayJoin)
