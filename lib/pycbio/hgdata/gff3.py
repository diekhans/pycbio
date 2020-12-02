"""
Object representation of GFF3 data and parser for GFF3 files.

See: http://www.sequenceontology.org/gff3.shtml
"""

import urllib.request
import urllib.parse
import urllib.error
import copy
import re
import collections
from pycbio.sys import PycbioException
from pycbio.sys import fileOps

GFF3_HEADER = "##gff-version 3"


class GFF3Exception(PycbioException):
    """
    Exception associated with GFF3 data.
    """
    def __init__(self, message, fileName=None, lineNumber=None, cause=None):
        if fileName is not None:
            message = "{}:{}: {}".format(fileName, lineNumber, message)
        super(GFF3Exception, self).__init__(message, cause)


# characters forcing encode for columns
_encodeColRegexpStr = "\t|\n|\r|%|[\x00-\x1F]|\x7f"
_encodeColRegexp = re.compile(_encodeColRegexpStr)

# characters forcing encode for attribute names or values
_encodeAttrReStr = _encodeColRegexpStr + "|;|=|&|,"
_encodeAttrRe = re.compile(_encodeAttrReStr)


def _encodeCol(v):
    """
    Encode a column if is has special characters.
    """
    if _encodeColRegexp.search(v):
        return urllib.parse.quote(v)
    else:
        return v


def _encodeAttr(v):
    """
    Encode a attribute name or value if is has special characters.
    """
    if _encodeAttrRe.search(v):
        return urllib.parse.quote(v)
    else:
        return v


class Feature(object):
    """
    One feature notation from a GFF3 file.  Coordinates are in zero-based, half-open.
    Missing attribute, as code by `.' in the file are stored as None.
    """

    __slots__ = ("seqname", "source", "type", "start", "end", "score",
                 "strand", "frame", "attrs", "gff3Set", "lineNumber",
                 "parents", "children")

    def __init__(self, seqname, source, type, start, end, score, strand,
                 frame, attrs, gff3Set, lineNumber=None):
        """
        The attrs field is a dict of lists/tupes as attrs maybe
        multi-valued.  Range should be one based and will be converted to
        zero-based, half-open.
        """
        self.seqname = seqname
        self.source = source
        self.type = type
        self.start = start - 1
        self.end = end
        self.score = score
        self.strand = strand
        self.frame = frame
        self.attrs = copy.deepcopy(attrs)
        self.gff3Set = gff3Set
        self.lineNumber = lineNumber
        self.parents = set()
        self.children = set()

    def __getstate__(self):
        return (self.seqname, self.source, self.type, self.start, self.end, self.score, self.strand, self.frame, self.attrs, self.gff3Set, self.lineNumber, self.parents, self.children)

    def __setstate__(self, state):
        self.seqname, self.source, self.type, self.start, self.end, self.score, self.strand, self.frame, self.attrs, self.gff3Set, self.lineNumber, self.parents, self.children = state

    @staticmethod
    def _dotIfNone(val):
        return val if val is not None else '.'

    def _attrStr(self, name):
        """
        Return name=value for a single attribute
        """
        return "{}={}".format(
            _encodeAttr(name),
            ",".join([_encodeAttr(v) for v in self.attrs[name]]))

    def _attrStrs(self):
        """
        Return name=value, semi-colon-separated string for attributes, including
        url-style quoting
        """
        return ";".join([self._attrStr(name)
                         for name in sorted(self.attrs.keys())])

    def __str__(self):
        """
        Return the object as a valid GFF3 record line.
        """
        return "\t".join([self.seqname, self.source, self.type,
                          str(self.start + 1), str(self.end), self._dotIfNone(self.score),
                          self._dotIfNone(self.strand), self._dotIfNone(self.frame),
                          self._attrStrs()])

    @property
    def featureId(self):
        """
        ID attribute or None if records doesn't have an ID
        """
        featId = self.attrs.get("ID")
        if featId is not None:
            featId = featId[0]
        return featId

    def getAttr1(self, name, default=None):
        """get a single valued attributes or default.  Error if multi-valued"""
        values = self.attrs.get(name)
        if values is None:
            return default
        if len(values) != 1:
            raise GFF3Exception("expected single valued attr: {}".format(name),
                                self.gff3Set.fileName, self.lineNumber)
        return values[0]

    def getRAttr(self, name):
        "get a require attributes list of values, error if not found"
        values = self.attrs.get(name)
        if values is None:
            raise GFF3Exception("required attribute not found: {}".format(name),
                                self.gff3Set.fileName, self.lineNumber)
        return values

    def getRAttr1(self, name):
        """get a require attributes with a single value, error if not found or multi-valued"""
        values = self.getRAttr(name)
        if len(values) != 1:
            raise GFF3Exception("expected single valued attr: {}".format(name),
                                self.gff3Set.fileName, self.lineNumber)
        return values[0]


class Gff3Set(object):
    """
    A set of GFF3 sequence annotations
    """
    def __init__(self, fileName=None):
        self.fileName = fileName
        self.roots = set()     # root nodes (those with out parents)
        # index of features by id. GFF3 allows disjoint features with
        # the same id.  None is used to store features without ids
        self.byFeatureId = collections.defaultdict(list)

    def add(self, feature):
        """
        Add a feature record
        """
        # None featureId allowed
        self.byFeatureId[feature.featureId].append(feature)

    def _linkFeature(self, feature):
        """
        Link a feature with it's parents.
        """
        parentIds = feature.attrs.get("Parent")
        if parentIds is None:
            self.roots.add(feature)
        else:
            for parentId in parentIds:
                self._linkToParent(feature, parentId)

    def _linkToParent(self, feature, parentId):
        """
        Link a feature with it's children
        """
        parentParts = self.byFeatureId.get(parentId)
        if parentParts is None:
            raise GFF3Exception("Parent feature does not exist: {}".format(parentId),
                                self.fileName, feature.lineNumber)
        # parent maybe disjoint
        for parentPart in parentParts:
            feature.parents.add(parentPart)
            parentPart.children.add(feature)

    def finish(self):
        """
        finish loading the set, constructing the tree
        """
        # features maybe disjoint
        for featureParts in list(self.byFeatureId.values()):
            for feature in featureParts:
                self._linkFeature(feature)

    @staticmethod
    def _recSortKey(r):
        return (r.seqname, r.start, -r.end, r.type)

    def _writeRec(self, fh, rec):
        fh.write(str(rec) + "\n")
        for child in sorted(rec.children, key=self._recSortKey):
            self._writeRec(fh, child)

    def write(self, fh):
        """
        Write set to a GFF3 format file.
        """
        fh.write(GFF3_HEADER + "\n")
        for root in sorted(self.roots, key=self._recSortKey):
            self._writeRec(fh, root)


class Gff3Parser(object):
    """
    Parser for GFF3 files.  This parse does basic validation, but does not
    fully test for conformance.
    """

    def __init__(self):
        self.fileName = self.lineNumber = None

    # parses `attr=val'; GFF3 spec is not very specific on the allowed values.
    SPLIT_ATTR_RE = re.compile("^([a-zA-Z][^=]*)=(.*)$")

    def _parseAttrVal(self, attrStr):
        """
        Returns tuple of tuple of (attr, value), multiple are returned to
        handle multi-value attributes.
        """
        m = self.SPLIT_ATTR_RE.match(attrStr)
        if m is None:
            raise GFF3Exception("can't parse attr/value: '" + attrStr + "'",
                                self.fileName, self.lineNumber)
        name = urllib.parse.unquote(m.group(1))
        val = m.group(2)
        # Split by comma separate then unquote.  Commas in values must be
        # url encoded.
        return (name, [urllib.parse.unquote(v) for v in val.split(',')])

    SPLIT_ATTR_COL_RE = re.compile("; *")

    def _parseAttrs(self, attrsStr):
        """
        Parse the attrs and values
        """
        attrs = dict()
        for attrStr in self.SPLIT_ATTR_COL_RE.split(attrsStr):
            name, vals = self._parseAttrVal(attrStr)
            if name in attrs:
                raise GFF3Exception("duplicated attribute name: {}".format(name),
                                    self.fileName, self.lineNumber)
            attrs[name] = vals
        return attrs

    GFF3_NUM_COLS = 9

    def _parseRecord(self, gff3Set, line):
        """
        Parse one record.
        """
        row = line.split("\t")
        if len(row) != self.GFF3_NUM_COLS:
            raise GFF3Exception(
                "Wrong number of columns, expected {}, got {}".format(
                    self.GFF3_NUM_COLS, len(row)),
                self.fileName, self.lineNumber)
        feature = Feature(urllib.parse.unquote(row[0]), urllib.parse.unquote(row[1]),
                          urllib.parse.unquote(row[2]),
                          int(row[3]), int(row[4]), row[5], row[6], row[7],
                          self._parseAttrs(row[8]), gff3Set, self.lineNumber)
        gff3Set.add(feature)

    # spaces or comment line
    IGNORED_LINE_RE = re.compile("(^[ ]*$)|(^[ ]*#.*$)")

    @staticmethod
    def _isIgnoredLine(line):
        return Gff3Parser.IGNORED_LINE_RE.search(line) is not None

    def _checkHeader(self, line):
        # split to allow multiple spaces and tabs
        if line.split() != GFF3_HEADER.split():
            raise GFF3Exception(
                "First line is not GFF3 header ({}), got: {}".format(
                    GFF3_HEADER, line), self.fileName, self.lineNumber)

    def _parseLine(self, gff3Set, line):
        if self.lineNumber == 1:
            self._checkHeader(line)
        elif not self._isIgnoredLine(line):
            self._parseRecord(gff3Set, line)

    def parse(self, gff3File, gff3Fh=None):
        """
        Parse the gff3 files and return a Gff3Set object in format.  If
        gff3File ends with .gz or .bz2, it will decompressed.  If gff3Fh is
        specified, then parse the already opened stream, with gff3File used
        for error message.
        """
        self.fileName = gff3File
        self.lineNumber = 0
        fh = fileOps.opengz(gff3File, 'r') if gff3Fh is None else gff3Fh
        try:
            gff3Set = Gff3Set(self.fileName)
            for line in fh:
                self.lineNumber += 1
                self._parseLine(gff3Set, line[0:-1])
        finally:
            self.fileName = self.lineNumber = None
            if gff3Fh is None:
                fh.close()
        gff3Set.finish()
        return gff3Set
