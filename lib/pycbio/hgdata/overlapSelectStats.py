# Copyright 2006-2012 Mark Diekhans
from pycbio.tsv import TsvTable, TsvReader

# inId	selectId	inOverlap	selectOverlap	overBases	similarity
typeMap = {
    "inOverlap": float,
    "selectOverlap": float,
    "overBases": int,
    "similarity": float}


class OverlapSelectStatsReader(TsvReader):
    "reader for output from overlapSelect -statsOutput"

    def __init__(self, fileName):
        super(OverlapSelectStatsReader, self).__init__(fileName, typeMap=typeMap)


class OverlapSelectStatsTbl(TsvTable):
    "table of overlapSelect -statsOutput results"
    def __init__(self, fileName):
        super(OverlapSelectStatsTbl, self).__init__(fileName, typeMap=typeMap, multiKeyCols=("inId", "selectId"))


__all__ = [OverlapSelectStatsReader.__name__, OverlapSelectStatsTbl.__name__]
