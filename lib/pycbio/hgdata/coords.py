# Copyright 2006-2012 Mark Diekhans
"browser coordinates object"

from __future__ import print_function
from collections import namedtuple


class CoordsError(Exception):
    "Coordinate error"
    pass


class Coords(namedtuple("Coords", ("name", "start", "end", "strand", "size"))):
    """Immutable sequence coordinates
    Fields:
       name, start, end - start/end maybe None to indicate a full sequence
       size - optional size of sequence
       strand - optional strand.
    """
    __slots__ = ()

    def __new__(cls, name, start, end, strand=None, size=None):
        return super(Coords, cls).__new__(cls, name, start, end, strand, size)

    @classmethod
    def __parse_parts(cls, coordsStr, size):
        cparts = coordsStr.split(":")
        name = cparts[0]
        if len(cparts) > 2:
            raise CoordsError("invalid start-end")
        if len(cparts) == 1:
            if size is None:
                return name, None, None
            else:
                return name, 0, size
        else:
            rparts = cparts[1].split("-")
            return name, int(rparts[0]), int(rparts[1])

    @classmethod
    def parse(cls, coordsStr, strand=None, size=None):
        """Construct an object from genome browser 'name:start-end'.
        If allowSimpleName is specified, then only 'name' can be used. The range
        will be None..None if size is not specified, otherwise 0..size"""
        try:
            if strand not in ('+', '-', None):
                raise CoordsError("invalid strand")
            name, start, end = cls.__parse_parts(coordsStr, size)
            return Coords(name, start, end, strand, size)
        except Exception as ex:
            raise CoordsError("invalid coordinates: \"{}\": {}".format(coordsStr, ex))

    def subrange(self, start, end):
        """Construct a Coords object that is a subrange of this one."""
        if (start > end) or (start < self.start) or (end > self.end):
            raise CoordsError("invalid subrange: {}-{} of {}".format(start, end, self))
        return Coords(self.name, start, end, self.strand, self.size)

    def __str__(self):
        if self.start is None:
            return self.name
        else:
            return "{}:{}-{}".format(self.name, self.start, self.end)

    def eqLoc(self, other):
        "is the strand location the same?"
        return ((self.name == other.name)
                and (self.start == other.start)
                and (self.end == other.end)
                and (self.strand == other.strand))

    def eqAbsLoc(self, other):
        "is the absolute location the same?"
        return ((self.name == other.name)
                and (self.start == other.start)
                and (self.end == other.end))

    def __hash__(self):
        return super(Coords, self).__hash__()

    def __eq__(self, other):
        return ((self.name == other.name)
                and (self.start == other.start)
                and (self.end == other.end)
                and (self.strand == other.strand)
                and (self.size == other.size))

    def __lt__(self, other):
        if self.name < other.name:
            return True
        elif self.start < other.start:
            return True
        elif self.end < other.end:
            return True
        elif self.strand < other.strand:
            return True
        else:
            return False

    def __len__(self):
        return self.end - self.start

    def overlaps(self, other):
        return ((self.name == other.name) and (self.start < other.end) and (self.end > other.start))

    def overlapsStrand(self, other):
        return self.overlaps(other) and (self.strand == other.strand)

    def reverse(self):
        """move coordinates to other strand"""
        if self.size is None:
            raise ValueError("reverse() requires size")
        elif self.strand is None:
            raise ValueError("reverse() requires strand")
        strand = '-' if self.strand == '+' else '+'
        return Coords(self.name,
                      self.size - self.end,
                      self.size - self.start,
                      strand=strand, size=self.size)

    def abs(self):
        "force to positive strand"
        if self.strand == '+':
            return self
        else:
            return self.reverse()

    def base(self):
        "return Coords with only name, start, and end set"
        if (self.strand is None) and (self.size is None):
            return self
        else:
            return Coords(self.name, self.start, self.end)
