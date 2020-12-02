# Copyright 2006-2012 Mark Diekhans
from pycbio.sys import PycbioException


class Subsets(object):
    "Generate possible subsets for a set of elements"

    def __init__(self, elements=None):
        """initialize set, optionally defining elements from a list or set of elements"""
        if elements is not None:
            self.elements = set(elements)
        else:
            self.elements = set()

        # lazy cache of subsets
        self.subsets = None

        # dict of inclusive subsets for each subset, built in a lazy manner
        self.inclusiveSubsets = None

    def add(self, element):
        "Add an element to the set, ignore ones that already exist"
        self.elements.add(element)
        self.subsets = None
        self.inclusiveSubsets = None

    @staticmethod
    def _subListSortKey(sub):
        "compare two subsets for sorting, first by length, then lexcelly"
        # first by length; then lexically
        return (len(sub), sorted(sub))

    def _makeSubset(self, bitSet, elements):
        "generated a subset for a bit set of the elements in list"
        iBit = 0
        bits = bitSet
        subset = list()
        while (bits != 0):
            if (bits & 1):
                subset.append(elements[iBit])
            bits = bits >> 1
            iBit += 1
        return frozenset(subset)

    def _makeSubsets(self, elements):
        "Build list of all of the possible subsets of a set using binary counting."
        # convert set input, as elements must be indexable for this algorithm
        if isinstance(elements, set) or isinstance(elements, frozenset):
            elements = list(elements)

        # build as lists for sorting
        nSubsets = (1 << len(elements)) - 1
        subsets = list()
        for bitSet in range(1, nSubsets + 1):
            subsets.append(self._makeSubset(bitSet, elements))
        # sort and constructs sets
        subsets.sort(key=self._subListSortKey)
        return tuple(subsets)

    def getSubsets(self):
        "get the subsets, building if needed"
        if self.subsets is None:
            self.subsets = self._makeSubsets(self.elements)
        return self.subsets

    def getSubset(self, wantSet):
        "search for the specified subset object, error if it doesn't exist"
        if self.subsets is None:
            self.subsets = self._makeSubsets(self.elements)
        for ss in self.subsets:
            if ss == wantSet:
                return ss
        raise PycbioException("not a valid subset: " + str(wantSet))

    def _makeInclusiveSubset(self, subset):
        "make an inclusive subset list for a subset"
        inclSubsets = []
        for iss in self._makeSubsets(subset):
            inclSubsets.append(iss)
        inclSubsets.sort(key=self._subListSortKey)
        return tuple(inclSubsets)

    def getInclusiveSubsets(self, subset):
        """Get the inclusive subsets for particular subset; that is all subsets
        that contain all of the specified sets."""
        if self.inclusiveSubsets is None:
            self.inclusiveSubsets = dict()
        inclSubsets = self.inclusiveSubsets.get(subset)
        if inclSubsets is None:
            inclSubsets = self._makeInclusiveSubset(subset)
            self.inclusiveSubsets[subset] = inclSubsets
        return inclSubsets
