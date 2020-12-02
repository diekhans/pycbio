# Copyright 2006-2012 Mark Diekhans
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

from collections import namedtuple
from pycbio.sys import PycbioException


def RemoveValueError(ValueError):
    "error when removed not found"
    def __init__(self, start, end):
        super(RemoveValueError, self).__init__("range {}-{} with specified value not found".format(start, end))


class Binner(object):
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


class Entry(namedtuple("Entry",
                       ("start", "end", "value"))):
    "entry associating a range with a value"
    __slots__ = ()

    def overlaps(self, start, end):
        "test if the range is overlapped by the entry"
        return (end > self.start) and (start < self.end)

    def __str__(self):
        return str(self.start) + "-" + str(self.end) + ": " + str(self.value)


class RangeBins(object):
    """Range indexed container for a single sequence.  This using a binning
    scheme that implements spacial indexing. Based on UCSC hg browser binRange
    C module.  """
    __slots__ = ("seqId", "strand", "buckets")

    def __init__(self, seqId, strand):
        self.seqId = seqId
        self.strand = strand
        self.buckets = {}  # indexed by bin, each bucket is a list

    def add(self, start, end, value):
        bin = Binner.calcBin(start, end)
        entries = self.buckets.get(bin)
        if entries is None:
            self.buckets[bin] = entries = []
        entries.append(Entry(start, end, value))

    def overlapping(self, start, end):
        "generator over values overlapping the specified range"
        if (start < end):
            for bins in Binner.getOverlappingBins(start, end):
                for j in range(bins[0], bins[1] + 1):
                    bucket = self.buckets.get(j)
                    if bucket is not None:
                        for entry in bucket:
                            if entry.overlaps(start, end):
                                yield entry.value

    def removeIfExists(self, start, end, value):
        """Remove an entry with the particular range if it exists, otherwise return false """
        try:
            bucket = self.buckets[(Binner.calcBin(start, end))]  # exception if no bucket
            bucket.remove(Entry(start, end, value))  # exception if no value
            return True
        except IndexError:
            return False
        except ValueError:
            return False

    def values(self):
        "generator over all values"
        for bin in list(self.buckets.values()):
            for entry in bin:
                yield entry.value

    def dump(self, fh):
        "print contents for debugging purposes"
        for bin in list(self.buckets.keys()):
            fh.write(self.seqId + " (" + str(self.strand) + ") bin=" + str(bin) + "\n")
            for entry in self.buckets[bin]:
                fh.write("\t" + str(entry) + "\n")


class RangeFinder(object):
    """Container index by sequence id, range, and optionally strand.
    All entries added to the object must either have strand or not
    have strand.  A query without strand will find all overlapping
    entries on either strand if strand was specified when adding entries.
    """
    validStrands = set((None, "+", "-"))

    def __init__(self):
        self.haveStrand = None
        self.seqBins = {}

    def _checkStrand(self, strand):
        if strand not in (None, "+", "-"):
            raise PycbioException("invalid strand: {}".format(strand))

    def add(self, seqId, start, end, value, strand=None):
        "add an entry for a sequence and range, and optional strand"
        self._checkStrand(strand)
        if self.haveStrand is None:
            self.haveStrand = (strand is not None)
        elif self.haveStrand != (strand is not None):
            raise PycbioException("all RangeFinder entries must either have strand or not have strand")
        key = (seqId, strand)
        bins = self.seqBins.get(key)
        if bins is None:
            self.seqBins[key] = bins = RangeBins(seqId, strand)
        bins.add(start, end, value)

    def _overlappingSpecificStrand(self, seqId, start, end, strand):
        "check overlap on specific strand, which might be None"
        bins = self.seqBins.get((seqId, strand))
        if bins is not None:
            for value in bins.overlapping(start, end):
                yield value

    def _overlappingBothStrands(self, seqId, start, end):
        "return range overlaps, checking both strands"
        for value in self._overlappingSpecificStrand(seqId, start, end, '+'):
            yield value
        for value in self._overlappingSpecificStrand(seqId, start, end, '-'):
            yield value

    def overlapping(self, seqId, start, end, strand=None):
        "generator over values overlaping the specified range on seqId, optional strand"
        self._checkStrand(strand)
        if self.haveStrand and (strand is None):
            # must check on both strands
            return self._overlappingBothStrands(seqId, start, end)
        else:
            # must only check a specifc strand, or no strand to check
            if not self.haveStrand:
                strand = None  # no strand to check
            return self._overlappingSpecificStrand(seqId, start, end, strand)

    def _removeIfExists(self, seqId, start, end, value, strand):
        removed = False
        bins = self.seqBins.get((seqId, strand))
        if bins is not None:
            removed = bins.removeIfExists(start, end, value)
        return removed

    def _removeSpecificStrand(self, seqId, start, end, value, strand):
        "remove an entry on specific strand, which might be None"
        if not self._removeIfExists(seqId, start, end, value, strand):
            raise RemoveValueError(start, end)

    def _removeBothStrands(self, seqId, start, end, value):
        "remove an entry, checking both strands"
        removed = self._removeIfExists(seqId, start, end, value, '+')
        if not removed:
            removed = self._removeIfExists(seqId, start, end, value, '-')
        if not removed:
            raise RemoveValueError(start, end)

    def remove(self, seqId, start, end, value, strand=None):
        """remove an entry with the particular range and value, value error if not found"""
        self._checkStrand(strand)
        if self.haveStrand and (strand is None):
            # must check on both strands
            self._removeBothStrands(seqId, start, end, value)
        else:
            # must only check a specifc strand, or no strand to check
            if not self.haveStrand:
                strand = None  # no strand to check
            self._removeSpecificStrand(seqId, start, end, value, strand)

    def values(self):
        "generator over all values"
        for bins in self.seqBins.values():
            for value in list(bins.values()):
                yield value

    def dump(self, fh):
        "print contents for debugging purposes"
        for bins in list(self.seqBins.values()):
            bins.dump(fh)


__all__ = (RemoveValueError.__name__, Binner.__name__, RangeFinder.__name__,)
