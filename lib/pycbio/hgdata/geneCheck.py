# Copyright 2006-2012 Mark Diekhans
from pycbio.tsv import TsvTable, TsvReader
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


# acc	chr	chrStart	chrEnd	strand	stat	frame	start	stop	orfStop	cdsGap	cdsMult3Gap	utrGap	cdsUnknownSplice	utrUnknownSplice	cdsNonCanonSplice	utrNonCanonSplice	numExons	numCds	numUtr5	numUtr3	numCdsIntrons	numUtrIntrons	nmd	causes
typeMap = {"chrStart": int,
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
    for gc in TsvReader(fspec, typeMap=typeMap):
        yield gc


class GeneCheckTbl(TsvTable):
    """Table of GeneCheck objects loaded from a Tsv.  acc index is build
    """

    def __init__(self, fileName, idIsUniq=False):
        self.idIsUniq = idIsUniq
        if idIsUniq:
            uniqKeyCols = "acc"
            multiKeyCols = None
        else:
            uniqKeyCols = None
            multiKeyCols = "acc"
        super(GeneCheckTbl, self).__init__(fileName, typeMap=typeMap, uniqKeyCols=uniqKeyCols, multiKeyCols=multiKeyCols)
        self.idIndex = self.indices.acc

    def _sameLoc(self, chk, chrom, start, end):
        return (chk is not None) and (chk.chr == chrom) and (chk.chrStart == start) and (chk.chrEnd == end)

    def getByGeneLoc(self, id, chrom, start, end):
        "get check record by id and location, or None if not found"
        if self.idIsUniq:
            chk = self.idIndex.get(id)
            if self._sameLoc(chk, chrom, start, end):
                return chk
        else:
            for chk in self.idIndex.get(id):
                if self._sameLoc(chk, chrom, start, end):
                    return chk
        return None

    def getById(self, id):
        """get check record by id or None if not found.  If idIsUniq was not specified,
        a list is returned"""
        return self.idIndex.get(id)

    def getByGenePred(self, gp):
        return self.getByGeneLoc(gp.name, gp.chrom, gp.txStart, gp.txEnd)
