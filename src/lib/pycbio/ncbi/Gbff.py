# Copyright 2006-2010 Mark Diekhans
from Bio.GenBank import LocationParser
from pycbio.sys import PycbioException

class GbffExcept(PycbioException):
    pass

def featFindQual(feat, key):
    "get the specified qualifier, or None"
    for qual in feat.qualifiers:
        if qual.key == key:
            return qual
    return None

def qualTrimVal(qual):
    if qual == None:
        return None
    val = qual.value
    if (val != None) and val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val

def featHaveQual(feat, key):
    "does a feature have a qualifier?"
    return (featFindQual(feat, key) != None)

def featGetQual(feat, key):
    "get the specified qualifier value, or None if not found.  Remove quotes if present"
    qual = featFindQual(feat, key)
    if qual == None:
        return None
    val = qual.value
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val
        
def featMustGetQual(feat, key):
    val = featGetQual(feat, key)
    if val == None:
        raise GbffExcept("qualifier \""+key+"\" not found in feature: " + str(feat))
    return val

def featGetQualByKeys(feat, keys):
    "get feature based on first matching key"
    for key in keys:
        val = featGetQual(feat, key)
        if val != None:
            return val
    return None
    
def featMustGetQualByKeys(feat, keys):
    "get feature based on first matching key, or error"
    val = featGetQualByKeys(feat, keys)
    if val == None:
        featRaiseNeedAQual(feat, keys)
    return val

def featRaiseNeedAQual(feat, keys):
   "raise error about one of the qualifiers not being found"
   raise GbffExcept("didn't find any of these qualifiers: "
                    + ", ".join(keys) + " in feature: " + str(feat))

def featGetGeneId(feat):
    "get a db_ref qualifier for GeneID, or None"
    for qual in feat.qualifiers:
        if (qual.key == "/db_xref=") and qual.value.startswith('"GeneID:'):
            return qualTrimVal(qual)
    return None

def featMustGetGeneId(feat):
    """get a db_ref qualifier for GeneID.  If it can't be found, but there is
    a LocusID, fake up a GeneID from the LocusID, or error if neither can occur"""
    # FIXME: still needed?
    val = featGetGeneId(feat)
    if val == None:
        val = featGetLocusId(feat)
        if val != None:
            prWarn("/db_xref GeneID not found in feature, using LocusID:", feat)
            val = "GeneID:" + val.split(":")[1]  # fake it
    if val == None:
        raise GbffExcept("/db_xref GeneID not found in feature: " + str(feat))
    return val

def featGetLocusId(feat):
    "get a db_ref qualifier for LocusId, or None"
    for qual in feat.qualifiers:
        if (qual.key == "/db_xref=") and qual.value.startswith('"LocusID:'):
            return qualTrimVal(qual)
    return None

def featGetGID(feat):
    "get a db_ref qualifier for GeneID, or None"
    for qual in feat.qualifiers:
        if (qual.key == "/db_xref=") and qual.value.startswith('"GI:'):
            return qualTrimVal(qual)
    return None

def featGetGIDIfFeat(feat):
    "get a db_ref qualifier for GeneID, or None if missing or feat is None"
    if feat == None:
        return None
    else:
         return featGetGID(feat)

def featGetCdsId(feat):
    "get a CDS identifier from qualifier, or None"
    return featGetQualByKeys(feat, ("/protein_id=", "/standard_name="))

class Coord(object):
    "[0..n) coord"
    __slots__ = ("start", "end", "strand")
    def __init__(self, start, end, strand):
        self.start = start
        self.end = end
        self.strand = strand

    def __str__(self):
        return str(self.start) + ".." + str(self.end) + "/"+str(self.strand)

    def size(self):
        return self.end-self.start

    def __cmp__(self, other):
        if not isinstance(other, Coord):
            return -1
        else:
            d = cmp(self.strand, other.strand)
            if d == 0:
                d = cmp(self.start, other.start)
                if d == 0:
                    d = cmp(self.end, other.end)
            return d

    def overlaps(self, other):
        return (self.start < other.end) and (self.end > other.start) and (self.strand == other.strand)

    def contains(self, other):
        return (other.start >= self.start) and (other.end <= self.end) and (self.strand == other.strand)

class Coords(list):
    "List of Coord objects"

    def __init__(self, init=None):
        if init != None:
            list.__init__(self, init)
            assert((len(self)==0) or isinstance(self[0], Coord))
        else:
            list.__init__(self)

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
        for i in xrange(len(self)):
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
            while  (si < len(self)) and (self[si].end < other[oi].start):
                si += 1
            if (si >= len(self)) or (self[si].start >= other[oi].end) or not self[si].contains(other[oi]):
                return False
            oi += 1
        return True

    @staticmethod
    def fromLocation(locSpec):
        """Convert Genbank location spec to Coords"""
        loc = LocationParser.parse(LocationParser.scan(locSpec))
        return Coords(Coords.__cnvLoc(loc))
            
    @staticmethod
    def __getPos(posObj):
        if isinstance(posObj, LocationParser.HighBound) or isinstance(posObj, LocationParser.LowBound):
            val = posObj.base
        else:
            val = posObj.val
        if isinstance(val, LocationParser.Integer):
            val = val.val
        return val

    @staticmethod
    def __cnvAbs(loc, strand):
        if loc.path != None:
            raise GbffExcept("don't know how to handel non-null path in: "+str(loc))
        # dig out start and end based on location class
        if isinstance(loc.local_location, LocationParser.Range):
            start = Coords.__getPos(loc.local_location.low)-1
            end = Coords.__getPos(loc.local_location.high)
        elif isinstance(loc.local_location, LocationParser.Integer):
            # single location
            start = start = loc.local_location.val-1
            end = start+1
        else:
            raise GbffExcept("__cnvAbs can't handle location class: " + str(loc.__class__))
        return Coord(start, end, strand)

    @staticmethod
    def __cnvLoc(loc, strand='+'):
        "convert to a list of Coord objects"
        if isinstance(loc, LocationParser.AbsoluteLocation):
            return [Coords.__cnvAbs(loc, strand)]
        elif isinstance(loc, LocationParser.Function):
            if loc.name == "complement":
                return Coords.__cnvLoc(loc.args, '-')
            if loc.name == "join":
                return Coords.__cnvLoc(loc.args, strand)
        elif isinstance(loc, list):
            coords = []
            for l in loc:
                coords.extend(Coords.__cnvLoc(l, strand))
            return coords
        else:
            raise GbffExcept("don't not how to convert location: " + str(loc))

