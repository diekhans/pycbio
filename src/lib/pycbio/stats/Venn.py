"Generate Venn diagram set intersection statistics"

from pycbio.stats.Subsets import Subsets

class SetDict(dict):
    "Dictionary of sets"

    def __init__(self, subsets=None):
        "sets can be pre-defined to allow for empty sets"
        if subsets != None:
            for ss in subsets:
                self[ss] = set()

    def add(self, key, val):
        "add a value to a set"
        if not key in self:
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
        if self.subsets == None:
            self.subsets = Subsets()

        # Tables mappings set name to items and items to set names
        self.nameToItems = SetDict()
        self.itemToNames = SetDict()

        # Venn table, dict index by name, of items (lazy build)
        self.venn = None

    def addItem(self, setName, item):
        "add a single item from a named set"
        self.subsets.add(setName)
        self.nameToItems.add(setName, item)
        self.itemToNames.add(item, setName)
        self.venn = None

    def addItems(self, setName, items):
        "add items from a named set"
        self.subsets.add(setName)
        for item in items:
            self.nameToItems.add(setName, item)
            self.itemToNames.add(item, setName)
        self.venn = None

    def _buildVenn(self):
        "build Venn table"
        self.venn = SetDict(self.subsets.getSubsets())

        for item in self.itemToNames.iterkeys():
            nameSet = frozenset(self.itemToNames[item])
            self.venn.add(nameSet, item)

    def _buildInclusive(self):
        "build as inclusive subsets"
        self.venn = SetDict(self.subsets.getSubsets())

        for item in self.itemNames.iterkeys():
            setName = self.itemNames[item]
            for iss in self.subsets.getInclusiveSubsets(setName):
                self.venn.add(iss, item)

    def _update(self):
        "build venn or inclusive venn, if it doesn't exists"
        if self.venn == None:
            if self.isInclusive:
                self._buildInclusive()
            else:
                self._buildVenn()

    def getSubsetIds(self, subset):
        "get ids for the specified subset"
        self._update()
        ids = self.venn.get(subset)
        if ids == None:
            ids = []
        return ids

    def getSubsetCounts(self, subset):
        "get counts for the specified subset"
        return len(self.getSubsetIds(subset))

