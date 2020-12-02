# Copyright 2006-2012 Mark Diekhans

# this module is tested by pycbio/src/progs/gbff/gbffGenesToGenePred

from pycbio.sys import PycbioException
from Bio import SeqFeature


class GbffExcept(PycbioException):
    pass


def featHaveQual(feat, key):
    "does a feature have a qualifier?"
    return (key in feat.qualifiers)


def featGetQual1(feat, key):
    """get the single valued qualifier, or None if not found.  Returns first
    value and error if qualifier has more than one value"""
    val = feat.qualifiers.get(key)
    if val is None:
        return None
    if len(val) != 1:
        raise GbffExcept("qualifier \"{}\" has multiple values".format(key))
    return val[0]


def featMustGetQual1(feat, key):
    val = featGetQual1(feat, key)
    if val is None:
        raise GbffExcept("qualifier \"{}\" not found in feature: {}".format(key, str(feat)))
    return val


def featGetQual1ByKeys(feat, keys):
    "get single-valued qualifier based on first matching key"
    for key in keys:
        val = featGetQual1(feat, key)
        if val is not None:
            return val
    return None


def featMustGetQual1ByKeys(feat, keys):
    "get a single valued qualifier based on first matching key, or error"
    val = featGetQual1ByKeys(feat, keys)
    if val is None:
        featRaiseNeedAQual(feat, keys)
    return val


def featRaiseNeedAQual(feat, quals):
    "raise error about one of the qualifiers not being found"
    raise GbffExcept("didn't find any of these qualifiers: {} in feature: {}".format(", ".join(quals), str(feat)))


def featGetDbXRef(feat, dbXRefPrefix):
    "return a dbXRef starting with dbXRefPrefix (include `:' in key), or None if not found"
    dbXRefs = feat.qualifiers.get("db_xref")
    if dbXRefs is not None:
        for dbXRef in dbXRefs:
            if dbXRef.startswith(dbXRefPrefix):
                return dbXRef[len(dbXRefPrefix):]
    return None


def featGetGeneId(feat):
    "get a db_ref qualifier for GeneID, or None"
    return featGetDbXRef(feat, "GeneID:")


def featMustGetGeneId(feat):
    """get a db_ref qualifier for GeneID or error if not found"""
    # FIXME: at one point returned locus id if gene id not found still needed?
    val = featGetGeneId(feat)
    if val is None:
        raise GbffExcept("db_xref GeneID not found in feature: {}".format(str(feat)))
    return val


def featGetLocusId(feat):
    "get a db_ref qualifier for LocusId, or None"
    return featGetDbXRef(feat, "LocusID:")


def featGetGID(feat):
    "get a db_ref qualifier for GI, or None"
    return featGetDbXRef(feat, "GI:")


def featGetCdsId(feat):
    "get a CDS identifier from qualifier, or None"
    return featGetQual1ByKeys(feat, ("protein_id", "standard_name"))


class Coord(object):
    "[0..n) coord"
    __slots__ = ("start", "end", "strand")

    def __init__(self, start, end, strand):
        "stand can be +/- or -1/+1, converted to +/-"
        self.start = start
        self.end = end
        if isinstance(strand, int):
            self.strand = "+" if (strand > 0) else "-"
        else:
            self.strand = strand

    def __str__(self):
        return "{}..{}/{}".format(self.start, self.end, self.strand)

    def size(self):
        return self.end - self.start

    def __eq__(self, other):
        return ((self.start == other.start)
                and (self.end == other.end)
                and (self.strand == other.strand))

    def __lt__(self, other):
        if self.start < other.start:
            return True
        if self.end < other.end:
            return True
        if self.strand < other.strand:
            return True
        return False

    def overlaps(self, other):
        return (self.start < other.end) and (self.end > other.start) and (self.strand == other.strand)

    def contains(self, other):
        return (other.start >= self.start) and (other.end <= self.end) and (self.strand == other.strand)

    @staticmethod
    def fromFeatureLocation(loc, strand):
        "convert to a FeatureLocation object to a Coord"
        return Coord(loc.start.position, loc.end.position, strand)


class Coords(list):
    "List of Coord objects"

    def __init__(self, init=None):
        super(Coords, self).__init__()
        if init is not None:
            self.extend(init)
        assert((len(self) == 0) or isinstance(self[0], Coord))

    def __str__(self):
        strs = []
        for c in self:
            strs.append(str(c))
        return ",".join(strs)

    def size(self):
        s = 0
        for c in self:
            s += c.size()
        return s

    def getRange(self):
        """get Coord covered by this object, which must be sorted"""
        if len(self) == 0:
            return None
        else:
            return Coord(self[0].start, self[-1].end, self[0].strand)

    def findContained(self, coord):
        "find index of first range containing coord, or None"
        for i in range(len(self)):
            if self[i].contains(coord):
                return i
        return None

    def isContained(self, other):
        """Are all blocks in other contained within blocks of self.  This
        doesn't check for all bases of the containing blocks being covered.
        This handles fame shift CDS, where a base in the mRNA block may not be
        covered."""

        oi = 0
        si = 0
        while oi < len(other):
            # find next self block containing other[oi]
            while (si < len(self)) and (self[si].end < other[oi].start):
                si += 1
            if (si >= len(self)) or (self[si].start >= other[oi].end) or not self[si].contains(other[oi]):
                return False
            oi += 1
        return True

    def _cnvSeqFeature(self, location, strand):
        self.append(Coord.fromFeatureLocation(location, strand))

    @staticmethod
    def fromSeqFeature(feat):
        """Convert Biopython SeqFeature object to Coords. This will handle sub_features"""
        isinstance(feat, SeqFeature.SeqFeature)
        coords = Coords()
        if isinstance(feat.location, SeqFeature.CompoundLocation):
            for location in feat.location.parts:
                coords._cnvSeqFeature(location, feat.strand)
        else:
            coords._cnvSeqFeature(feat.location, feat.strand)
        coords.sort()
        return coords
