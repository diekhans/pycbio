"""
Cigar parsers and operations.
"""
from __future__ import print_function
from builtins import str
from builtins import range
import re
from collections import namedtuple

# FIXME: make immutable


OP_ALIGNED = 'M'  # match or mismatch
OP_TINSERT = 'I'  # target insert
OP_TDELETE = 'D'  # target deletion


class Cigar(list):
    """cigar parser and representation.  Derived class implement specific
    cigar encodings"""

    OpType = namedtuple("OpType", ("count", "code"))

    def __init__(self, cigarStr, validOps):
        self.extend(self.__parseCigar(cigarStr, validOps))

    def __str__(self):
        opStrs = []
        for op in self:
            if op.count != 1:
                opStrs.append(str(op.count))
            opStrs.append(str(op.code))
        return "".join(opStrs)

    def __parseOp(self, cigarStr, validOps, opParts):
        if opParts[0] != "":
            self.__invalidCigar
            raise TypeError("Invalid cigar string at '{}' : {}".format("".join(opParts), cigarStr))
        try:
            cnt = 1 if opParts[1] == "" else int(opParts[1])
        except ValueError:
            raise TypeError("Invalid cigar string at '{}' : {}".format("".join(opParts), cigarStr))
        op = opParts[2].upper()
        if op not in validOps:
            raise TypeError("Invalid cigar string, unknown operation '{}' : {}".format("".join(opParts), cigarStr))
        return Cigar.OpType(cnt, op)

    def __parseCigar(self, cigarStr, validOps):
        # remove white space first, then convert to (count, op).  Re split will
        # result in triples of ("", count, op), where count might be empty.
        # Also as a trailing space.
        parts = re.split("([0-9]*)([A-Za-z])",
                         re.sub("\\s+", "", cigarStr))
        if ((len(parts) - 1) % 3) != 0:
            raise TypeError("Invalid cigar string, doesn't parse into a valid cigar: {}".format(cigarStr))
        return tuple([self.__parseOp(cigarStr, validOps, parts[i:i + 3])
                      for i in range(0, len(parts) - 1, 3)])


class ExonerateCigar(Cigar):
    "exonerate cigar string"
    validOps = frozenset([OP_ALIGNED, OP_TINSERT, OP_TDELETE])

    def __init__(self, cigarStr):
        super(ExonerateCigar, self).__init__(cigarStr, ExonerateCigar.validOps)

# FIXME: gencode-icedb/bin/cdnaEnsemblAligns2 has pslFromCigar, might move to here
