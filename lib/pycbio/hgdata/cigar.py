"""
Cigar parsers and operations.
"""
import re
from collections import namedtuple


class CigarRun(namedtuple("CigarRun", ("code", "count"))):
    "CIGAR run-length encoding"
    __slots__ = ()

    # operation codes
    ALIGNED = 'M'  # match or mismatch
    TINSERT = 'I'  # target insert
    TDELETE = 'D'  # target deletion

    @property
    def aligned(self):
        "is this an aligned block?"
        return self.code == self.ALIGNED

    @property
    def tinsert(self):
        "is this a target insert block?"
        return self.code == self.TINSERT

    @property
    def tdelete(self):
        "is this a target deletion block?"
        return self.code == self.TDELETE

    @property
    def qinsert(self):
        "is this a query insert block?"
        return self.code == self.TDELETE

    @property
    def qdelete(self):
        "is this a query query block?"
        return self.code == self.TINSERT


class Cigar(tuple):
    """Cigar parser and representation.  Derived class implement specific
    cigar encodings"""

    def __new__(cls, cigarStr, validOps):
        return super(Cigar, cls).__new__(cls, cls._parseCigar(cigarStr, validOps))

    def __str__(self):
        opStrs = []
        for op in self:
            if op.count != 1:
                opStrs.append(str(op.count))
            opStrs.append(str(op.code))
        return "".join(opStrs)

    @classmethod
    def _parseCigar(cls, cigarStr, validOps):
        # remove white space first, then convert to (count, op).  Re split will
        # result in triples of ("", count, op), where count might be empty.
        # Also as a trailing space.
        parts = re.split("([0-9]*)([A-Za-z])", re.sub("\\s+", "", cigarStr))
        if ((len(parts) - 1) % 3) != 0:
            raise TypeError("Invalid cigar string, doesn't parse into a valid cigar: {}".format(cigarStr))
        return (cls._parseOp(cigarStr, validOps, parts[i:i + 3])
                for i in range(0, len(parts) - 1, 3))

    @classmethod
    def _parseOp(cls, cigarStr, validOps, opParts):
        if opParts[0] != "":
            raise TypeError("Invalid cigar string at '{}' : {}".format("".join(opParts), cigarStr))
        try:
            cnt = 1 if opParts[1] == "" else int(opParts[1])
        except ValueError:
            raise TypeError("Invalid cigar string at '{}' : {}".format("".join(opParts), cigarStr))
        op = opParts[2].upper()
        if op not in validOps:
            raise TypeError("Invalid cigar string, unknown operation '{}' : {}".format("".join(opParts), cigarStr))
        return CigarRun(op, cnt)


class ExonerateCigar(Cigar):
    "exonerate cigar string"
    validOps = frozenset([CigarRun.ALIGNED, CigarRun.TINSERT, CigarRun.TDELETE])

    def __new__(cls, cigarStr):
        return super(ExonerateCigar, cls).__new__(cls, cigarStr, ExonerateCigar.validOps)
