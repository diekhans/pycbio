"""
Cigar parsers and operations.
"""
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
        
    @staticmethod
    def __invalidCigar(msg, cigarStr):
        raise TypeError("Invalid cigar string, {}: {}".format(msg, cigarStr))

    def __parseOp(self, cigarStr, validOps, opParts):
        if opParts[0] != "":
            raise TypeError("Invalid cigar string, {} at '{}' : {}".format(msg, "".join(opParts), cigarStr))
        try:
            cnt = 1 if opParts[1] == "" else int(opParts[1])
        except ValueError, ex:
            raise TypeError("Invalid cigar string, {} at '{}' : {}".format(msg, "".join(opParts), cigarStr))
        op = opParts[2].upper()
        if not op in validOps:
            raise TypeError("Invalid cigar string, {} unknown operation '{}' : {}".format(msg, "".join(opParts), cigarStr))
        return Cigar.OpType(cnt, op)
        
    def __parseCigar(self, cigarStr, validOps):
        # remove white space first, then convert to (count, op).  Re split will
        # result in triples of ("", count, op), where count might be empty.
        # Also as a trailing space.
        parts = re.split("([0-9]*)([A-Za-z])",
                         re.sub("\\s+", "", cigarStr))
        if ((len(parts)-1) % 3) != 0:
            self.__invalidCigar("doesn't parse into a valid cigar", cigarStr)
        return tuple([self.__parseOp(cigarStr, validOps, parts[i:i+3])
                      for i in xrange(0, len(parts)-1, 3)])

class ExonerateCigar(Cigar):
    "exonerate cigar string"
    validOps = frozenset([OP_ALIGNED, OP_TINSERT, OP_TDELETE])

    def __init__(self, cigarStr):
        super(ExonerateCigar, self).__init__(cigarStr, ExonerateCigar.validOps)


    
# /* create a PSL from an ENSEMBL-style cigar formatted alignment */
# static struct psl* pslFromCigar(char *qName, int qSize, int qStart, int qEnd,
#                                 char *tName, int tSize, int tStart, int tEnd,
#                                 char *strand, char *cigar) {
#     int blocksAlloced = 4;
#     struct psl *psl = pslNew(qName, qSize, qStart, qEnd, tName, tSize, tStart, tEnd, strand, blocksAlloced, 0);

#     char cigarSpec[strlen(cigar+1)];  // copy since parsing is destructive
#     strcpy(cigarSpec, cigar);
#     char *cigarNext = cigarSpec;
#     char op;
#     int size;
#     int qNext = qStart, qBlkEnd = qEnd;
#     if (strand[0] == '-') {
#         reverseIntRange(&qNext, &qBlkEnd, qSize);
#     }
#     int tNext = tStart, tBlkEnd = tEnd;
#     if (strand[1] == '-') {
#         reverseIntRange(&tNext, &tBlkEnd, tSize);
#     }

#     while (getNextCigarOp(&cigarNext, &op, &size)) {
#         switch (op) {
#         case 'M': // match or mismatch (gapless aligned block)
#             if (psl->blockCount == blocksAlloced)
#                 pslGrow(psl, &blocksAlloced);
            
#             psl->blockSizes[psl->blockCount] = size;
#             psl->qStarts[psl->blockCount] = qNext;
#             psl->tStarts[psl->blockCount] = tNext;
#             psl->blockCount++;
#             psl->match += size;
#             tNext += size;
#             qNext += size;
#             break;
#         case 'I': // inserted in target
#             tNext += size;
#             psl->tNumInsert++;
#             psl->tBaseInsert += size;
#             break;
#         case 'D': // deleted from target
#             qNext += size;
#             psl->qNumInsert++;
#             psl->qBaseInsert += size;
#             break;

#         default:
#             errAbort("invalid CIGAR op %c in %s", op, cigar);
#         }
#     }
#     if (qNext != qBlkEnd) {
#         errAbort("CIGAR length does not match aligned query range: %s %s", qName, cigar);
#     }
#     if (tNext != tBlkEnd) {
#         errAbort("CIGAR length does not match aligned target range: %s %s", qName, cigar);
#     }
#     if (psl->strand[1] == '-') {
#         pslRc(psl);
#     }
#     psl->strand[1] = '\0';
#     return psl;
# }

    
