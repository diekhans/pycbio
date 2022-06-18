# Copyright 2006-2012 Mark Diekhans
"browser coordinates object"

from collections import namedtuple
from functools import total_ordering
from pycbio import PycbioException


class CoordsError(PycbioException):
    "Coordinate error"
    pass


def reverseRange(start, end, size):
    if size is None:
        raise ValueError("reversing strand requires size")
    return (size - end), (size - start)


def reverseStrand(strand):
    if strand is None:
        return None
    else:
        return '+' if strand == '-' else '-'


def _intOrNone(v):
    return v if v is None else int(v)


@total_ordering
class Coords(namedtuple("Coords", ("name", "start", "end", "strand", "size"))):
    """Immutable sequence coordinates
    Fields:
       name - sequence name
       start, end - zero-based, half-open range
       strand - optional strand
       size - optional size of sequence
    """
    __slots__ = ()

    def __new__(cls, name, start, end, strand=None, size=None):
        if not ((start <= end) and (start >= 0)):
            raise CoordsError(f"invalid range: {start}..{end}")
        if not ((size is None) or (end <= size)):
            raise CoordsError(f"range: {start}..{end} exceeds size {size}")
        return super(Coords, cls).__new__(cls, name, _intOrNone(start), _intOrNone(end), strand, _intOrNone(size))

    def __getnewargs_ex__(self):
        return ((self.name, self.start, self.end, self.strand, self.size), {})

    @classmethod
    def _parse_parts(cls, coordsStr, oneBased):
        cparts = coordsStr.split(":")
        name = cparts[0]
        if len(cparts) != 2:
            raise CoordsError(f"range missing, expect chr:start-end: '{coordsStr}'")
        startStr, endStr = cparts[1].split("-")
        start = int(startStr.replace(',', ''))
        if oneBased:
            start -= 1
        end = int(endStr.replace(',', ''))
        return name, start, end

    @classmethod
    def parse(cls, coordsStr, strand=None, size=None, oneBased=False):
        """Construct an object from genome browser 'name:start-end' or 'name".
        If only a simple names is specified without a size, the range
        will be None..None, with a size it will be 0..size.  Commas in numbers
        are removed. If one-based is True, it the value be convert zero-base, 1/2 open"""
        try:
            if strand not in ('+', '-', None):
                raise CoordsError(f"invalid strand: '{strand}'")
            name, start, end = cls._parse_parts(coordsStr, oneBased)
            return Coords(name, start, end, strand, size)
        except Exception as ex:
            raise CoordsError(f"invalid coordinates: '{coordsStr}'") from ex

    def subrange(self, start, end, strand=None):
        """Construct a Coords object that is a subrange of this one.  If strand is provided,
        then the coordinates will be reversed if to match current strand, otherwise strand
        is assumed to be the same as self.strand"""
        if (strand is not None) and (strand != self.strand):
            start, end = reverseRange(start, end, self.size)
        if (start > end) or (start < self.start) or (end > self.end):
            raise CoordsError("invalid subrange: {}-{} of {}".format(start, end, self))
        return Coords(self.name, start, end, self.strand, self.size)

    def adjrange(self, start, end):
        """Construct a Coords object that has an adjust range on the same sequence
        and strand.
        """
        return Coords(self.name, start, end, self.strand, self.size)

    def format(self, *, oneBased=False, commas=False):
        if self.start is None:
            return self.name
        else:
            fmt = "{}:{}-{}" if not commas else "{}:{:,}-{:,}"
            return fmt.format(self.name, self.start + (1 if oneBased else 0), self.end)

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
        elif self.name > other.name:
            return False
        elif self.start < other.start:
            return True
        elif self.start > other.start:
            return False
        elif self.end < other.end:
            return True
        elif self.end > other.end:
            return False
        elif (self.strand is None) and (other.strand is None):
            return False
        elif (self.strand is None) and (other.strand is not None):
            return True  # no strand sorts low
        elif (self.strand is not None) and (other.strand is None):
            return False
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

    @property
    def absStart(self):
        "get start of positive strand"
        return self.start if self.strand == '+' else self.size - self.end

    @property
    def absEnd(self):
        "get end of positive strand"
        return self.end if self.strand == '+' else self.size - self.start

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
        """Intersection range, or None if not on same chromosome, zero length if not intersected"""
        # FIXME: need to define for different strand
        # FIXME: should this return zero-length if on different chrom?
        self._checkCmpType(other)
        if self.name != other.name:
            return None
        else:
            start = max(self.start, other.start)
            end = min(self.end, other.end)
            if start > end:
                start = end
            return Coords(self.name, start, end, self.strand, self.size)

    def contains(self, other):
        "is other fully contained in this object, ignoring strand"
        self._checkCmpType(other)
        return (other.name == self.name) and (other.start >= self.start) and (other.end <= other.end)
