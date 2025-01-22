# Copyright 2006-2025 Mark Diekhans
from collections import defaultdict
from pycbio.tsv import TsvReader
from pycbio.sys.symEnum import SymEnum

def statParse(val):
    "parse a value of the stat column (ok or err)"
    if val == "ok":
        return True
    elif val == "err":
        return False
    else:
        raise ValueError("invalid stat column value: \"" + val + "\"")

def statFmt(val):
    "format a value of the stat column (ok or err)"
    if val:
        return "ok"
    else:
        return "err"


statType = (statParse, statFmt)

def startStopParse(val):
    "parse value of the start or stop columns (ok or no)"
    if val == "ok":
        return True
    elif val == "no":
        return False
    else:
        raise ValueError("invalid start/stop column value: \"" + val + "\"")

def startStopFmt(val):
    "format value of the start or stop columns (ok or no)"
    if val:
        return "ok"
    else:
        return "no"


startStopType = (startStopParse, startStopFmt)

def nmdParse(val):
    "parse value of the NMD column (ok or nmd)"
    if val == "ok":
        return True
    elif val == "nmd":
        return False
    else:
        raise ValueError("invalid nmd column value: \"" + val + "\"")

def nmdFmt(val):
    "format value of the NMD column (ok or nmd)"
    if val:
        return "ok"
    else:
        return "nmd"


nmdType = (nmdParse, nmdFmt)

def strOrNone(val):
    "return None if val is zero length otherwise val"
    if len(val) == 0:
        return None
    else:
        return val

def strListSplit(commaStr):
    "parser for comma-separated string list into a list"
    if len(commaStr) == 0:
        return []
    strs = commaStr.split(",")
    return strs


def strListJoin(strs):
    "formatter for a list into a comma seperated string"
    if strs is not None:
        return ",".join(strs)
    else:
        return ""


strListType = (strListSplit, strListJoin)

# frame status
FrameStat = SymEnum("FrameStat",
                    ("ok", "bad", "mismatch", "discontig", "noCDS"))


# checkId	acc	chr	chrStart	chrEnd	strand	stat	frame	start	stop	orfStop	cdsGap	cdsMult3Gap	utrGap	cdsUnknownSplice	utrUnknownSplice	cdsNonCanonSplice	utrNonCanonSplice	numExons	numCds	numUtr5	numUtr3	numCdsIntrons	numUtrIntrons	nmd	causes
checkTypeMap = {
    "checkId": int,
    "chrStart": int,
    "chrEnd": int,
    "stat": statType,
    "frame": FrameStat,
    "start": startStopType,
    "stop": startStopType,
    "orfStop": int,
    "cdsGap": int,
    "cdsMult3Gap": int,
    "utrGap": int,
    "cdsUnknownSplice": int,
    "utrUnknownSplice": int,
    "cdsNonCanonSplice": int,
    "utrNonCanonSplice": int,
    "cdsSplice": int,   # old column
    "utrSplice": int,   # old column
    "numExons": int,
    "numCds": int,
    "numUtr5": int,
    "numUtr3": int,
    "numCdsIntrons": int,
    "numUtrIntrons": int,
    "nmd": nmdType,
    "causes": strListType}


def GeneCheckReader(fspec):
    for gc in TsvReader(fspec, typeMap=checkTypeMap):
        yield gc


# checkId	acc	problem	info	chr	chrStart	chrEnd
detailsTypeMap = {
    "checkId": int,
    "info": strOrNone,
    "chrStart": int,
    "chrEnd": int}

def GeneCheckDetailsReader(fspec):
    for gc in TsvReader(fspec, typeMap=detailsTypeMap):
        yield gc

class GeneCheckTbl(list):
    """Table of GeneCheck objects loaded from a Tsv.  acc index is built,
    which is not assumed to be unique..
    """

    def __init__(self, checkTsv, detailsTsv=None):
        self.byCheckId = {}
        self.byAcc = defaultdict(list)
        self.detailsByCheckId = None

        self._loadChecks(checkTsv)
        if detailsTsv is not None:
            self._loadDetails(detailsTsv)

    def _loadChecks(self, checkTsv):
        for rec in GeneCheckReader(checkTsv):
            self.append(rec)
            self.byCheckId[rec.checkId] = rec
            self.byAcc[rec.acc].append(rec)
        self.byAcc.default_factory = None

    def _loadDetails(self, detailsTsv):
        self.detailsByCheckId = defaultdict(list)
        for rec in GeneCheckDetailsReader(detailsTsv):
            self.detailsByCheckId[rec.checkId].append(rec)
        self.detailsByCheckId.default_factory = None

    def findByAcc(self, acc):
        """get check record list by acc or None if not found."""
        return self.byAcc.get(acc)

    def getByAcc(self, acc):
        """get check record list by acc or error if not found."""
        return self.byAcc[acc]

    def haveDetails(self):
        return self.detailsByCheckId is not None

    def getDetails(self, geneCheck):
        """return list of details, if loaded, or None if there
        are no checks for this gene.
        """
        return self.detailsByCheckId.get(geneCheck.checkId)
