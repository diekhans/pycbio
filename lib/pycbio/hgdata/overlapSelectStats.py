# Copyright 2006-2026 Mark Diekhans
from collections import defaultdict
from pycbio.tsv import TsvReader

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


class OverlapSelectStatsTbl(list):
    """table of overlapSelect -statsOutput results, with the rows also indexed
    by inId and by selectId.  Each index maps a value to the list of rows with
    that value; neither column is unique."""

    def __init__(self, fileName):
        super(OverlapSelectStatsTbl, self).__init__(OverlapSelectStatsReader(fileName))
        self.byInId = self._buildIndex("inId")
        self.bySelectId = self._buildIndex("selectId")

    def _buildIndex(self, column):
        idx = defaultdict(list)
        for row in self:
            idx[getattr(row, column)].append(row)
        idx.default_factory = None
        return idx


__all__ = [OverlapSelectStatsReader.__name__, OverlapSelectStatsTbl.__name__]
