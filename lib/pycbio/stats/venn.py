# Copyright 2006-2022 Mark Diekhans
"Generate Venn diagram set intersection statistics"

from pycbio.stats.subsets import Subsets
from pycbio.sys import fileOps

# FIXME: confusing terminolog
#  setName vs items can
#  venn, vs subsets
#  id vs name
#


class SetDict(dict):
    "Dictionary of sets"

    def __init__(self, subsets=None):
        """sets can be pre-defined to allow for empty sets or shared subsets
        objects"""
        if subsets is not None:
            for ss in subsets:
                self[ss] = set()

    def add(self, key, val):
        "add a value to a set"
        if key not in self:
            self[key] = set()
        self[key].add(val)


class Venn(object):
    """Generate Venn diagram set intersections.  Each set has
    list of ids associated with it that are shared between sets.
    """

    def __init__(self, subsets=None, isInclusive=False):
        """create new Venn.  If subsets is None, a private Subsets object is
        created,"""

        # is this a standard venn or inclusive?
        self.isInclusive = isInclusive
        self.subsets = subsets
        if self.subsets is None:
            self.subsets = Subsets()

        # Tables mappings set name to items and items to set names
        self.nameToItems = SetDict()
        self.itemToNames = SetDict()

        # Venn table, dict index by name, of items (lazy build)
        self._venn = None

    def addItem(self, setName, item):
        "add a single item from a named set"
        self.subsets.add(setName)
        self.nameToItems.add(setName, item)
        self.itemToNames.add(item, setName)
        self._venn = None

    def addItems(self, setName, items):
        "add items from a named set"
        self.subsets.add(setName)
        for item in items:
            self.nameToItems.add(setName, item)
            self.itemToNames.add(item, setName)
        self._venn = None

    def getNumItems(self):
        return len(self.itemToNames)

    def _buildVenn(self):
        "build Venn table"
        self._venn = SetDict(self.subsets.getSubsets())

        for item in list(self.itemToNames.keys()):
            nameSet = frozenset(self.itemToNames[item])
            self._venn.add(nameSet, item)

    def _buildInclusive(self):
        "build as inclusive subsets"
        self._venn = SetDict(self.subsets.getSubsets())

        for item in list(self.itemToNames.keys()):
            setName = frozenset(self.itemToNames[item])
            for iss in self.subsets.getInclusiveSubsets(setName):
                self._venn.add(iss, item)

    def _update(self):
        "build venn or inclusive venn, if it doesn't exists"
        if self._venn is None:
            if self.isInclusive:
                self._buildInclusive()
            else:
                self._buildVenn()

    def getSubsetIds(self, subset):
        "get ids for the specified subset"
        self._update()
        ids = self._venn.get(subset)
        if ids is None:
            ids = []
        return ids

    def getSubsetCounts(self, subset):
        "get counts for the specified subset"
        return len(self.getSubsetIds(subset))

    def getTotalCounts(self):
        "get total of counts for all subsets (meaningless on inclusive)"
        t = 0
        for subset in self.subsets.getSubsets():
            t += self.getSubsetCounts(subset)
        return t

    @staticmethod
    def formatSubsetName(subset, subsetNameSeparator=" ", setNameFormatter=str):
        return subsetNameSeparator.join(sorted([setNameFormatter(s) for s in subset]))

    def writeCounts(self, fh, *, subsetNameSeparator=" ", setNameFormatter=str, excludeEmpty=False):
        "write TSV of subset counts to an open file"
        fileOps.prRowv(fh, "subset", "count")
        for subset in self.subsets.getSubsets():
            cnt = self.getSubsetCounts(subset)
            if (cnt > 0) or (not excludeEmpty):
                fileOps.prRowv(fh, self.formatSubsetName(subset, subsetNameSeparator, setNameFormatter), cnt)

    def writeSets(self, fh, *, subsetNameSeparator=" ", setNameFormatter=str, excludeEmpty=False):
        "write TSV of subsets and ids to an open file"
        # FIXME: same code as above
        fileOps.prRowv(fh, "subset", "ids")
        for subset in self.subsets.getSubsets():
            cnt = self.getSubsetCounts(subset)
            if (cnt > 0) or (not excludeEmpty):
                fileOps.prRowv(fh, self.formatSubsetName(subset, subsetNameSeparator, setNameFormatter), cnt)

    def _getCountRow(self, setNames, subset, count, setNameFormatter):
        return [1 if sn in subset else 0 for sn in setNames] + [count]

    def writeCountMatrix(self, fh, *, setNameFormatter=str, countColumn="count", excludeEmpty=False):
        "write matrix TSV, which each set being a column, along with count column"
        setNames = sorted(self.nameToItems.keys())
        fileOps.prRow(fh, [setNameFormatter(sn) for sn in setNames] + [countColumn])
        for subset in self.subsets.getSubsets():
            cnt = self.getSubsetCounts(subset)
            if (cnt > 0) or (not excludeEmpty):
                fileOps.prRow(fh, self._getCountRow(setNames, subset, cnt, setNameFormatter))
