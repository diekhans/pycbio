# Copyright 2006-2012 Mark Diekhans
"""Module to access output of pslStats UCSC browser command"""
from collections import defaultdict
from pycbio.tsv import TsvReader
from pycbio.sys.symEnum import SymEnum

# align is:
#  #qName	qSize	tName	tStart	tEnd	ident	qCover	repMatch	tCover
# query is:
#  #qName	qSize	alnCnt	minIdent	maxIdent	meanIdent	minQCover	maxQCover	meanQCover	minRepMatch	maxRepMatch	meanRepMatch	minTCover	maxTCover
# overall is:
#  #queryCnt	minQSize	maxQSize	meanQSize	alnCnt	minIdent	maxIdent	meanIdent	minQCover	maxQCover	meanQCover	minRepMatch	maxRepMatch	meanRepMatch	minTCover	maxTCover	aligned	aligned1	alignedN	totalAlignedSize

typeMap = {
    "qSize": int,
    "tStart": int,
    "tEnd": int,
    "ident": float,
    "qCover": float,
    "repMatch": float,
    "tCover": float,
    "alnCnt": int,
    "minIdent": float,
    "meanIdent": float,
    "minQCover": float,
    "maxQCover": float,
    "meanQCover": float,
    "maxRepMatch": float,
    "meanRepMatch": float,
    "minTCover": float,
    "queryCnt": int,
    "minQSize": int,
    "maxQSize": int,
    "meanQSize": int,
    "maxIdent": float,
    "minRepMatch": float,
    "maxTCover": float,
    "aligned": int,
    "aligned1": int,
    "alignedN": int,
    "totalAlignedSize": int,
}

class PslStatsType(SymEnum):
    """type of pslStats output"""
    ALIGN = 1
    QUERY = 2
    OVERALL = 3

class PslStats(list):
    """object to access output of pslStats command.  There are
    three different version: alignment stats: per-alignment,
    per-query, and overall.  This reads all three, however the
    columns and indent are different for each. """
    def __init__(self, pslStatsFile):
        tsvRdr = TsvReader(pslStatsFile, typeMap=typeMap)
        self.columns = tsvRdr.columns
        self.type = self._determineType(tsvRdr)
        self.idx = self._createIdx(self.type)
        for row in tsvRdr:
            self._add(row)

    @staticmethod
    def _determineType(tsv):
        if "totalAlignedSize" in tsv.colMap:
            return PslStatsType.OVERALL
        elif "alnCnt" in tsv.colMap:
            return PslStatsType.QUERY
        else:
            return PslStatsType.ALIGN

    @staticmethod
    def _createIdx(pslStatsType):
        if pslStatsType == PslStatsType.ALIGN:
            return defaultdict(list)
        elif pslStatsType == PslStatsType.QUERY:
            return {}
        else:
            return None

    def _add(self, row):
        self.append(row)
        if self.type == PslStatsType.ALIGN:
            self.idx[row.qName].append(row)
        elif self.type == PslStatsType.QUERY:
            self.idx[row.qName] = row
