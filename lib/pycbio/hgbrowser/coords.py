# Copyright 2006-2012 Mark Diekhans
"browser coordinates object"

from pycbio.sys.immutable import Immutable

# FIXME: support MAF db.chrom syntax, single base syntax, etc.


class CoordsError(Exception):
    "Coordinate error"
    pass


class Coords(Immutable):
    """Browser coordinates
    Fields:
       chrom, start, end - start/end maybe None to indicate a full chromosome
       db - optional genome assembly database
       chromSize - optional size of chromosome
       strand - optional strand
    """
    __slots__ = ("chrom", "start", "end", "db", "chromSize", "strand")

    def __parseCombined__(self, coordsStr):
        "parse chrom:start-end "
        try:
            self.chrom, rng = str.split(coordsStr, ":")
            self.start, self.end = str.split(rng, "-")
            self.start = int(self.start)
            self.end = int(self.end)
        except Exception as ex:
            raise CoordsError("invalid coordinates: \"" + str(coordsStr) + "\": " + str(ex))

    def __parseThree__(self, chrom, start, end):
        "parse chrom, start, end. start/end maybe strings, int or None  "
        try:
            self.chrom = chrom
            self.start = int(start) if start is not None else None
            self.end = int(end) if end is not None else None
        except Exception as ex:
            raise CoordsError("invalid coordinates: \"{}:{}-{}\": {}".format(chrom, start, end, ex))

    def __init__(self, *args, **kwargs):
        """args are either one argument in the form chr:start-end, or
        chr, start, end. options are db= and chromSize="""
        Immutable.__init__(self)
        if len(args) == 1:
            self.__parseCombined__(args[0])
        elif len(args) == 3:
            self.__parseThree__(args[0], args[1], args[2])
        else:
            raise CoordsError("Coords() excepts either one or three arguments")
        self.db = kwargs.get("db")
        self.chromSize = kwargs.get("chromSize")
        self.strand = kwargs.get("strand")
        self.mkImmutable()

    def __str__(self):
        return self.chrom + ":" + str(self.start) + "-" + str(self.end)

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
    
    def __cmp__(self, other):
        if other is None:
            return -1
        d = cmp(self.db, other.db)
        if d == 0:
            d = cmp(self.chrom, other.chrom)
        if d == 0:
            d = cmp(self.start, other.start)
        if d == 0:
            d = cmp(self.end, other.end)
        return d

    def __hash__(self):
        return hash(self.db) + hash(self.chrom) + hash(self.start)
