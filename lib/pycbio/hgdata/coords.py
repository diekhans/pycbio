# Copyright 2006-2012 Mark Diekhans
"browser coordinates object"

from collections import namedtuple
from pycbio.sys import PycbioException


class CoordsError(PycbioException):
    "Coordinate error"
    pass


def reverseRange(start, end, size):
    if size is None:
        raise ValueError("reversing strand requires size")
    return (size - end), (size - start)


def reverseStrand(strand):
    "None is assumed as +"
    return '+' if strand == '-' else '-'


def _intOrNone(v):
    return v if v is None else int(v)


class Coords(namedtuple("Coords", ("name", "start", "end", "strand", "size"))):
    """Immutable sequence coordinates
    Fields:
       name, start, end - start/end maybe None to indicate a full sequence
       strand - Strand, if it is None.
       size - optional size of sequence
    """
    __slots__ = ()

    def __new__(cls, name, start, end, strand=None, size=None):
        return super(Coords, cls).__new__(cls, name, _intOrNone(start), _intOrNone(end), strand, _intOrNone(size))

    @classmethod
    def _parse_parts(cls, coordsStr, size):
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
        """Construct an object from genome browser 'name:start-end' or 'name".
        If only a simple names is specified without a size, the range
        will be None..None, with a size it will be 0..size"""
        try:
            if strand not in ('+', '-', None):
                raise CoordsError("invalid strand")
            name, start, end = cls._parse_parts(coordsStr, size)
            return Coords(name, start, end, strand, size)
        except Exception as ex:
            raise CoordsError("invalid coordinates: \"{}\": {}".format(coordsStr, ex))

    def subrange(self, start, end, strand=None):
        """Construct a Coords object that is a subrange of this one.  If strand is provided,
        then the coordinates will be reversed if to match current strand, otherwise strand
        is assumed to be the same as self.strand"""
        if (strand is not None) and (strand != self.strand):
            start, end = reverseRange(start, end, self.size)
        if (start > end) or (start < self.start) or (end > self.end):
            raise CoordsError("invalid subrange: {}-{} of {}".format(start, end, self))
        return Coords(self.name, start, end, self.strand, self.size)

    def __str__(self):
        if self.start is None:
            return self.name
        else:
            return "{}:{}-{}".format(self.name, self.start, self.end)

    def _checkCmpType(self, other):
        if not isinstance(other, Coords):
            raise TypeError("can't compare Coord objects with {} objects".format(type(other).__name__))

    def eqLoc(self, other):
        "is the strand location the same?"
        self._checkCmpType(other)
        return ((self.name == other.name)
                and (self.start == other.start)
                and (self.end == other.end)
                and (self.strand == other.strand))

    def eqAbsLoc(self, other):
        "is the absolute location the same?"
        self._checkCmpType(other)
        if (self.name != other.name):
            return False
        elif self.strand == other.strand:
            return (self.start == other.start) and (self.end == other.end)
        elif self.size is not None:
            return ((self.size - self.end) == other.start) and ((self.size - self.start) == other.end)
        elif other.size is not None:
            return (self.start == (other.size - other.size)) and (self.end == (other.size - other.start))
        else:
            return False

    def __hash__(self):
        return super(Coords, self).__hash__()

    def __eq__(self, other):
        self._checkCmpType(other)
        return ((self.name == other.name)
                and (self.start == other.start)
                and (self.end == other.end)
                and (self.strand == other.strand)
                and (self.size == other.size))

    def __lt__(self, other):
        self._checkCmpType(other)
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
        "overlap regardless of strand"
        self._checkCmpType(other)
        if self.name != other.name:
            return False
        elif (self.strand == other.strand) or (self.strand is None) or (other.strand is None):
            return (self.start < other.end) and (self.end > other.start)
        elif (self.strand is None) and (other.strand == '-'):
            return (self.start < (other.size - other.start)) and (self.end > (other.size - other.end))
        elif (self.strand == '-') and (other.strand is None):
            return ((self.size - self.end) < other.end) and ((self.size - self.start) > other.start)
        else:
            assert self.strand != other.strand
            return False

    def overlapsStrand(self, other):
        self._checkCmpType(other)
        return (self.strand == other.strand) and self.overlaps(other)

    def reverse(self):
        """move coordinates to other strand. None strand is assumed +"""
        if self.size is None:
            raise ValueError("reverse() requires size")
        return Coords(self.name,
                      self.size - self.end,
                      self.size - self.start,
                      strand=reverseStrand(self.strand),
                      size=self.size)

    def abs(self):
        "convert to positive strand if on negative strand"
        if self.strand == '-':
            return self.reverse()
        else:
            return self

    def adjust(self, **kwargs):
        "return version with any field update via keyword arguments"
        fields = {k: getattr(self, k) for k in self._fields}
        fields.update(kwargs)
        return Coords(**fields)

    def base(self):
        "return Coords with only name, start, and end set"
        if (self.strand is None) and (self.size is None):
            return self
        else:
            return Coords(self.name, self.start, self.end)

    def intersect(self, other):
        """Intersection range, or non if not on same chromosome."""
        # FIXME: need to define for different strand
        self._checkCmpType(other)
        if self.name != other.name:
            return None
        else:
            start = max(self.start, other.start)
            end = min(self.end, other.end)
            if start > end:
                start = end
            return Coords(self.name, start, end, self.strand, self.size)
