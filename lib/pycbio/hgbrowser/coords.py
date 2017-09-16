# Copyright 2006-2012 Mark Diekhans
"browser coordinates object"

from __future__ import print_function
from collections import namedtuple

# FIXME: support MAF db.chrom syntax, single base syntax, etc.
# FIXME: use factory methods instead of __init trying to figure it out
# FIXME: make generic, don't use chrom, use seq


class CoordsError(Exception):
    "Coordinate error"
    pass


class Coords(namedtuple("Coords", ("chrom", "start", "end", "db", "chromSize", "strand"))):
    """Browser coordinates
    Fields:
       chrom, start, end - start/end maybe None to indicate a full chromosome
       db - optional genome assembly database
       chromSize - optional size of chromosome
       strand - optional strand
    """
    __slots__ = ()

    def __new__(cls, chrom, start, end, db=None, chromSize=None, strand=None):
        return super(Coords, cls).__new__(cls, chrom, start, end, db, chromSize, strand)

    @staticmethod
    def parse(coordsStr, db=None, chromSize=None, strand=None):
        "construct an object from genome browser chrom:start-end type string"
        try:
            chrom, rng = str.split(coordsStr, ":")
            start, end = str.split(rng, "-")
            return Coords(chrom, int(start), int(end), db, chromSize, strand)
        except Exception as ex:
            raise CoordsError("invalid coordinates: \"" + str(coordsStr) + "\": " + str(ex))

    def __str__(self):
        return self.chrom + ":" + str(self.start) + "-" + str(self.end)

    def __lt__(self, other):
        "less than, ignoring strand"
        if self.chrom < other.chrom:
            return True
        if self.start < other.start:
            return True
        if self.end < other.end:
            return True
        return False

    @property
    def name(self):
        # FIXME: need to generalizes this
        return self.chrom

    def size(self):
        return self.end - self.start

    def overlaps(self, other):
        return ((self.chrom == other.chrom) and (self.start < other.end) and (self.end > other.start))

    def pad(self, frac=0.05, minBases=5):
        """return Coords, padded with a fraction of the range."""
        amt = int(frac * (self.end - self.start))
        if amt < minBases:
            amt = minBases
        st = self.start - amt
        if st < 0:
            st = 0
        return Coords(self.chrom, st, self.end + amt)

    def reverse(self):
        """move coordinates to other strand"""
        if self.chromSize is None:
            raise ValueError("reverse requires chromSize")
        if self.strand == '+':
            strand = '-'
        elif self.strand == '-':
            strand = '+'
        else:
            strand = self.strand  # would keep weird value
        return Coords(self.chrom,
                      self.chromSize - self.end,
                      self.chromSize - self.start,
                      db=self.db, chromSize=self.chromSize, strand=strand)
