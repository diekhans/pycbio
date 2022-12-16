# Copyright 2006-2022 Mark Diekhans
"""Container index by sequence id, range, and optionally strand that
efficiently searches for overlapping entries.  Also contains code for
generating SQL where clauses to restrict by bin."""

##
# This code is a python reimplementation of binRange.{h,c} and hdb.c written
# by Jim Kent.
##

# from C code:
# There's a bin for each 128k (1<<17) segment. The next coarsest is 8x as big
# (1<<13).  That is for each 1M segment, for each 8M segment, for each 64M
# segment, for each 512M segment, and one top level bin for 4Gb.  Note, since
# start and end are int's, the practical limit is up to 2Gb-1, and thus, only
# four result bins on the second level. A range goes into the smallest bin it
# will fit in.

import sys
from collections import namedtuple
from deprecation import deprecated
from pycbio import PycbioException


class RangeFinderException(PycbioException):
    """Exception from RangeFinder"""
    pass

class _EntryNotFound(Exception):
    "low-level indication of entry found"
    pass

class RemoveValueError(ValueError):
    "error when removed not found"
    def __init__(self, seqId, strand, entry):
        super(RemoveValueError, self).__init__(f"entry to remove not found: {seqId}:{entry.start}-{entry.end} strand={strand}, value: {repr(entry.value)}")


class Binner:
    "functions to translate ranges to bin numbers"

    binOffsetsBasic = (512 + 64 + 8 + 1,
                       64 + 8 + 1,
                       8 + 1,
                       1, 0)
    binOffsetsExtended = (4096 + 512 + 64 + 8 + 1,
                          512 + 64 + 8 + 1,
                          64 + 8 + 1, 8 + 1,
                          1, 0)

    binFirstShift = 17  # How much to shift to get to finest bin.
    binNextShift = 3    # How much to shift to get to next larger bin.

    binBasicMaxEnd = 512 * 1024 * 1024
    binOffsetToExtended = 4681

    @staticmethod
    def _calcBinForOffsets(start, end, baseOffset, offsets):
        "get the bin for a range"
        startBin = start >> Binner.binFirstShift
        endBin = (end - 1) >> Binner.binFirstShift
        for binOff in offsets:
            if (startBin == endBin):
                return baseOffset + binOff + startBin
            startBin >>= Binner.binNextShift
            endBin >>= Binner.binNextShift
        raise Exception("can't compute bin: start {}, end {} out of range".format(start, end))

    @staticmethod
    def calcBin(start, end):
        "get the bin for a range"
        if end <= Binner.binBasicMaxEnd:
            return Binner._calcBinForOffsets(start, end, 0, Binner.binOffsetsBasic)
        else:
            return Binner._calcBinForOffsets(start, end, Binner.binOffsetToExtended, Binner.binOffsetsExtended)

    @staticmethod
    def _getOverlappingBinsForOffsets(start, end, baseOffset, offsets):
        "generate bins for a range given a list of offsets"
        startBin = start >> Binner.binFirstShift
        endBin = (end - 1) >> Binner.binFirstShift
        for offset in offsets:
            yield (startBin + baseOffset + offset, endBin + baseOffset + offset)
            startBin >>= Binner.binNextShift
            endBin >>= Binner.binNextShift

    @staticmethod
    def getOverlappingBins(start, end):
        """Generate bins for the range.  Each value is closed range of (startBin, endBin)"""
        if end <= Binner.binBasicMaxEnd:
            # contained in basic range
            for bins in Binner._getOverlappingBinsForOffsets(start, end, 0, Binner.binOffsetsBasic):
                yield bins
            yield (Binner.binOffsetToExtended, Binner.binOffsetToExtended)
        else:
            if start < Binner.binBasicMaxEnd:
                # overlapping both basic and extended
                for bins in Binner._getOverlappingBinsForOffsets(start, Binner.binBasicMaxEnd, 0, Binner.binOffsetsBasic):
                    yield bins
            for bins in Binner._getOverlappingBinsForOffsets(start, end, Binner.binOffsetToExtended, Binner.binOffsetsExtended):
                yield bins

    @staticmethod
    def getOverlappingSqlExpr(binCol, seqCol, startCol, endCol, seq, start, end):
        """generate an SQL expression for overlaps with the specified range
        in order to efficiently query, there should be an index on (seqName, bin)
        """
        # build bin parts
        parts = []
        for bins in Binner.getOverlappingBins(start, end):
            if bins[0] == bins[1]:
                parts.append("({}={})".format(binCol, bins[0]))
            else:
                parts.append("({}>={} and {}<={})".format(binCol, bins[0], binCol, bins[1]))
        return "(({}=\"{}\") and ({}<{}) and ({}>{}) and ({}))".format(seqCol, seq, startCol, end, endCol, start, " or ".join(parts))


class _Entry(namedtuple("Entry",
                        ("start", "end", "value"))):
    "entry associating a range with a value"
    __slots__ = ()

    def overlaps(self, start, end):
        "test if the range is overlapped by the entry"
        return (end > self.start) and (start < self.end)

    def __str__(self):
        return str(self.start) + "-" + str(self.end) + ": " + str(self.value)


class RangeBins:
    """Range indexed container for a single sequence.  This using a binning
    scheme that implements spacial indexing. Based on UCSC hg browser binRange
    C module."""
    __slots__ = ("seqId", "strand", "minStart", "maxEnd", "buckets")

    def __init__(self, seqId, strand):
        self.seqId = seqId
        self.strand = strand
        self.minStart = sys.maxsize
        self.maxEnd = 0
        self.buckets = {}  # indexed by bin, each bucket is a list of _Entry objects

    def add(self, entry):
        bin = Binner.calcBin(entry.start, entry.end)
        entries = self.buckets.get(bin)
        if entries is None:
            self.buckets[bin] = entries = []
        entries.append(entry)
        self.minStart = min(self.minStart, entry.start)
        self.maxEnd = max(self.maxEnd, entry.end)

    def _mergeEntries(self, newEntry, overEntries, mergeFunc):
        for e in overEntries:
            self.remove(e)
        entries = [newEntry] + overEntries
        return _Entry(min((e.start for e in entries)),
                      max((e.end for e in entries)),
                      mergeFunc([e.value for e in entries]))

    def addMerge(self, entry, mergeFunc):
        overEntries = list(self.overlapping(entry.start, entry.end))  # must make copy
        if len(overEntries) > 0:
            entry = self._mergeEntries(entry, overEntries, mergeFunc)
        self.add(entry)

    def overlapping(self, start, end):
        "generator of entries overlapping the specified range"
        if (start < end):
            for bins in Binner.getOverlappingBins(start, end):
                for j in range(bins[0], bins[1] + 1):
                    bucket = self.buckets.get(j)
                    if bucket is not None:
                        for entry in bucket:
                            if entry.overlaps(start, end):
                                yield entry

    def remove(self, entry):
        """Remove an entry with the particular range and value"""
        try:
            bucket = self.buckets[(Binner.calcBin(entry.start, entry.end))]  # exception if no bucket
            bucket.remove(entry)  # exception if no value
        except (IndexError, ValueError):
            raise _EntryNotFound()

    def values(self):
        "generator over all values"
        for bin in self.buckets.values():
            for entry in bin:
                yield entry.value

    def dump(self, fh):
        "print contents for debugging purposes"
        for bin in list(self.buckets.keys()):
            fh.write(self.seqId + " (" + str(self.strand) + ") bin=" + str(bin) + "\n")
            for entry in self.buckets[bin]:
                fh.write("\t" + str(entry) + "\n")


class RangeFinder:
    """Container index by sequence id, range, and optionally strand.
    All entries added to the object must either have strand or not
    have strand.  A query without strand will find all overlapping
    entries on either strand if strand was specified when adding entries.
    """
    validStrands = set((None, "+", "-"))

    def __init__(self, *, mergeFunc=None):
        "mergeFunc must take a list of values and returned a new value"
        self.mergeFunc = mergeFunc
        self.haveStrand = None
        self.seqBins = {}

    def _checkStrand(self, strand):
        if strand not in (None, "+", "-"):
            raise RangeFinderException(f"invalid strand: '{strand}'")

    @staticmethod
    def _binKey(seqId, strand):
        return (seqId, strand)

    def _getBin(self, seqId, strand):
        "return None if no bin for seq+strand"
        return self.seqBins.get(self._binKey(seqId, strand))

    def _getBinsForAdd(self, seqId, start, end, strand):
        "setup for adding entries"
        self._checkStrand(strand)
        if self.haveStrand is None:
            self.haveStrand = (strand is not None)
        elif self.haveStrand != (strand is not None):
            raise RangeFinderException("all RangeFinder entries must all either have strand or not have strand")
        key = self._binKey(seqId, strand)
        bins = self.seqBins.get(key)
        if bins is None:
            self.seqBins[key] = bins = RangeBins(seqId, strand)
        return bins

    def add(self, seqId, start, end, value, strand=None):
        "add an entry for a sequence and range, and optional strand"
        bins = self._getBinsForAdd(seqId, start, end, strand)
        bins.add(_Entry(start, end, value))

    def addMerge(self, seqId, start, end, value, strand=None):
        """add an entry for a sequence and range, and optional strand,
        merging with existing overlapping entries"""
        if self.mergeFunc is None:
            raise RangeFinderException("RangeFinder does not have a mergeFunc, can't merge entries")
        bins = self._getBinsForAdd(seqId, start, end, strand)
        bins.addMerge(_Entry(start, end, value), self.mergeFunc)

    def addCoords(self, coords, value, strand=None):
        """Added using Coords object.  Note that coords.strands is direction
        for sequence, not orientation of annotation on a strand"""
        if coords.strand == '-':
            coords = coords.reverse()
        self.add(coords.name, coords.start, coords.end, value, strand)

    def _overlappingSpecificStrand(self, seqId, start, end, strand):
        "check overlap on specific strand, which might be None"
        bins = self.seqBins.get((seqId, strand))
        if bins is not None:
            for entry in bins.overlapping(start, end):
                yield entry.value

    def _overlappingBothStrands(self, seqId, start, end):
        "return range overlaps, checking both strands"
        yield from self._overlappingSpecificStrand(seqId, start, end, '+')
        yield from self._overlappingSpecificStrand(seqId, start, end, '-')

    def overlapping(self, seqId, start, end, strand=None):
        "generator over values overlapping the specified range on seqId, optional strand"
        self._checkStrand(strand)
        if self.haveStrand and (strand is None):
            # must check on both strands
            return self._overlappingBothStrands(seqId, start, end)
        else:
            # must only check a specifc strand, or no strand to check
            if not self.haveStrand:
                strand = None  # no strand to check
            return self._overlappingSpecificStrand(seqId, start, end, strand)

    def overlappingByCoords(self, coords):
        """generator over values overlapping using a Coords object"""
        return self.overlapping(coords.name, coords.start, coords.end, coords.strand)

    def _removeFromSeqBin(self, seqId, strand, entry):
        # strand maybe None
        self.seqBins.get((seqId, strand)).remove(entry)

    def _removeBothStrands(self, seqId, entry):
        "remove an entry, checking both strands"
        try:
            self._removeFromSeqBin(seqId, '+', entry)
        except _EntryNotFound:
            self._removeFromSeqBin(seqId, '-', entry)

    def _remove(self, seqId, strand, entry):
        if self.haveStrand and (strand is None):
            # must check on both strands
            self._removeBothStrands(seqId, entry)
        else:
            # must only check a specifc strand, or no strand to check
            if not self.haveStrand:
                strand = None  # no strand to check
            self._removeFromSeqBin(seqId, strand, entry)

    def remove(self, seqId, start, end, value, strand=None):
        """remove an entry with the particular range and value, value error if not found"""
        self._checkStrand(strand)
        entry = _Entry(start, end, value)
        try:
            self._remove(seqId, strand, entry)
        except _EntryNotFound:
            raise RemoveValueError(seqId, strand, entry)

    def values(self):
        "generator over all values"
        for bins in self.seqBins.values():
            yield from bins.values()

    def getSeqIds(self):
        """get set of sequences"""
        return frozenset([k[0] for k in self.seqBins.keys()])

    @deprecated()
    def getSeqs(self):
        return self.getSeqIds()

    def getSeqRange(self, seqId, strand=None):
        """Return the minimum start and maximum end for a given sequence.  Useful for
        look for closest entry by checking range.  If strand is not None and
        we have strands in bins, return just for that strand, otherwise for
        sequence regardless of strand.  Returns (None, None) if sequence is not
        present"""

        def _getRange(seqId, keyStrand):
            bins = self._getBin(seqId, keyStrand)
            if bins is None:
                return None, None
            else:
                return bins.minStart, bins.maxEnd

        self._checkStrand(strand)
        if not self.haveStrand:
            return _getRange(seqId, None)
        elif strand is None:
            r1 = _getRange(seqId, '+')
            if r1[0] is None:
                return None, None  # don't have seqId
            r2 = _getRange(seqId, '-')
            return (min(r1[0], r2[0]), max(r1[1], r2[1]))
        else:
            return _getRange(seqId, strand)

    def dump(self, fh):
        "print contents for debugging purposes"
        for bins in list(self.seqBins.values()):
            bins.dump(fh)


__all__ = (RemoveValueError.__name__, RangeFinderException.__name__,
           Binner.__name__, RangeFinder.__name__,)
