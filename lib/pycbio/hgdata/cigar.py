"""
Cigar parsers and operations.
"""
import re
from collections import namedtuple

# See
# SAM manual
# https://github.com/NBISweden/GAAS/blob/master/annotation/knowledge/cigar.md

CIGAR_DESC = """
|----+-----------------------------------+---------+---------+----------------+-------|
| OP | Description                       | Consume | Consume | Name           | index |
|    |                                   | query   | ref     |                |       |
|----+-----------------------------------+---------+---------+----------------+-------|
| M  | alignment match/mismatch          | yes     | yes     | BAM_CMATCH     |     0 |
| I  | insertion to the reference        | yes     | no      | BAM_CINS       |     1 |
| D  | deletion from the reference       | no      | yes     | BAM_CDEL       |     2 |
| N  | skipped region from the reference | no      | yes     | BAM_CREF_SKIP  |     3 |
| S  | soft clipping                     | yes     | no      | BAM_CSOFT_CLIP |     4 |
| H  | hard clipping                     | no      | no      | BAM_CHARD_CLIP |     5 |
| P  | padding                           | no      | no      | BAM_CPAD       |     6 |
| =  | sequence match                    | yes     | yes     | BAM_CEQUAL     |     7 |
| X  | sequence mismatch                 | yes     | yes     | BAM_CDIFF      |     8 |
| B  | in pysam, not specification       |         |         | BAM_CBACK      |     9 |
|----+-----------------------------------+---------+---------+----------------+-------|
"""

CIGAR_OPS = "MIDNSHP=X"  # index order
consumeQueryOps = frozenset(['M', 'I', 'S', '=', 'X'])
consumeQueryHardOps = frozenset(consumeQueryOps | frozenset(['H']))
consumeTargetOps = frozenset(['M', 'D', 'N', '=', 'X'])
validOps = frozenset(CIGAR_OPS)

class CigarRun(namedtuple("CigarRun", ("code", "count"))):
    "CIGAR run-length encoding"
    __slots__ = ()

    @property
    def aligned(self):
        "is this an aligned block?, match or mismatch"
        return self.code in ('M', '=', 'X')

    @property
    def tinsert(self):
        "is this a target insert block?"
        return self.code in ('D', 'N')

    @property
    def tdelete(self):
        "is this a target deletion block?"
        return self.code == 'I'

    @property
    def qinsert(self):
        "is this a query insert block?"
        return self.code == 'I'

    @property
    def qdelete(self):
        "is this a query deletion block?"
        return self.code in ('D', 'N')

    @property
    def intron(self):
        "is this an intron? (not in Ensembl)"
        return self.code == 'N'

    @property
    def match(self):
        """is this a match? (not in Ensembl, maybe others, check aligned as well)"""
        return self.code == '='

    @property
    def mismatch(self):
        """is this a mismatch?  (not in Ensembl, maybe others, check aligned as well)"""
        return self.code == 'X'

    @property
    def softclip(self):
        "soft clipped?"
        return self.code == 'S'

    @property
    def hardclip(self):
        "hard clipped?"
        return self.code == 'H'

    @property
    def consumesQuery(self):
        return self.code in consumeQueryOps

    @property
    def consumesQueryHard(self):
        return self.code in consumeQueryHardOps

    @property
    def consumesTarget(self):
        return self.code in consumeTargetOps

def _parseOp(cigarStr, opParts):
    try:
        if opParts[0] != "":
            raise ValueError()
        cnt = 1 if opParts[1] == "" else int(opParts[1])
    except ValueError:
        raise TypeError("Invalid cigar string at '{}' : {}".format("".join(opParts), cigarStr))
    op = opParts[2].upper()
    if op not in validOps:
        raise TypeError("Invalid cigar string, unknown operation '{}' : {}".format("".join(opParts), cigarStr))
    return CigarRun(op, cnt)

def _parseCigar(cigarStr):
    # remove white space first, then convert to (count, op).  Re split will
    # result in triples of ("", count, op), where count might be empty.
    # Also as a trailing space.
    parts = re.split("([0-9]*)([A-Za-z=])", re.sub("\\s+", "", cigarStr))
    if ((len(parts) - 1) % 3) != 0:
        raise TypeError("Invalid cigar string, doesn't parse into a valid cigar: {}".format(cigarStr))
    return (_parseOp(cigarStr, parts[i:i + 3])
            for i in range(0, len(parts) - 1, 3))

class Cigar(tuple):
    """Cigar parser and parsed representation."""

    def __new__(cls, cigarStr):
        return super(Cigar, cls).__new__(cls, _parseCigar(cigarStr))

    def __str__(self):
        return self.format()

    def format(self, *, inclOnes=False):
        """produce a cigar string.  If inclOnes
        is True, then include run counts of 1."""
        opStrs = []
        for op in self:
            if inclOnes or (op.count != 1):
                opStrs.append(str(op.count))
            opStrs.append(str(op.code))
        return "".join(opStrs)
