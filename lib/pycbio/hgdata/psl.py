# Copyright 2006-2012 Mark Diekhans
import re
from pycbio.hgdata.autoSql import intArraySplit, intArrayJoin, strArraySplit, strArrayJoin
from pycbio.tsv.tabFile import TabFileReader
from pycbio.hgdata import dnaOps
from pycbio.hgdata.cigar import ExonerateCigar
from collections import defaultdict
from deprecation import deprecated

# FIXME: drop sequence support, it is almost never used

# Notes:
#  - terms plus and minus are used because `positive' is long and `pos' abbreviation is
#    often used for position.


def reverseCoords(start, end, size):
    return (size - end, size - start)

def reverseStrand(s):
    "return reverse of a strand character"
    return "+" if (s == "-") else "-"

def dropQueryUniq(qName):
    """if a suffix in the form -[0-9]+(.[0-9]+)? is append to make the name unique,
    drop it"""
    return re.match('^(.+?)(-[0-9]+(.[0-9]+)*)?$', qName).group(1)

class PslBlock(object):
    """Block of a PSL"""
    __slots__ = ("psl", "iBlk", "qStart", "tStart", "size", "qSeq", "tSeq")

    def __init__(self, qStart, tStart, size, qSeq=None, tSeq=None):
        "sets iBlk base on being added in ascending order"
        self.psl = None
        self.iBlk = None
        self.qStart = qStart
        self.tStart = tStart
        self.size = size
        self.qSeq = qSeq
        self.tSeq = tSeq

    def __len__(self):
        return self.size

    def __str__(self):
        return "{}..{} <=> {}..{}".format(self.qStart, self.qEnd, self.tStart, self.tEnd)

    @property
    def qEnd(self):
        return self.qStart + self.size

    @property
    def tEnd(self):
        return self.tStart + self.size

    @property
    def qStartPlus(self):
        "get qStart for the block on positive strand"
        if self.psl.qStrand == '+':
            return self.qStart
        else:
            return self.psl.qSize - self.qEnd

    @property
    def qEndPlus(self):
        "get qEnd for the block on positive strand"
        if self.psl.qStrand == '+':
            return self.qEnd
        else:
            return self.psl.qSize - self.qStart

    @property
    def tStartPlus(self):
        "get tStart for the block on positive strand"
        if self.psl.tStrand == '+':
            return self.tStart
        else:
            return self.psl.tSize - self.tEnd

    @property
    def tEndPlus(self):
        "get tEnd for the block on positive strand"
        if self.psl.tStrand == '+':
            return self.tEnd
        else:
            return self.psl.tSize - self.tStart

    @deprecated()
    def getQStartPos(self):
        return self.qStartPlus

    @deprecated()
    def getQEndPos(self):
        return self.qEndPlus

    @deprecated()
    def getTStartPos(self):
        return self.tStartPlus

    @deprecated()
    def getTEndPos(self):
        return self.tEndPlus

    def sameAlign(self, other):
        "compare for equality of alignment."
        return (other is not None) and (self.qStart == other.qStart) and (self.tStart == other.tStart) and (self.size == other.size) and (self.qSeq == other.qSeq) and (self.tSeq == other.tSeq)

    def reverseComplement(self, newPsl):
        "construct a block that is the reverse complement of this block"
        return PslBlock(self.psl.qSize - self.qEnd,
                        self.psl.tSize - self.tEnd, self.size,
                        (dnaOps.reverseComplement(self.qSeq) if (self.qSeq is not None) else None),
                        (dnaOps.reverseComplement(self.tSeq) if (self.tSeq is not None) else None))

    def swapSides(self, newPsl):
        "construct a block with query and target swapped "
        return PslBlock(self.tStart, self.qStart, self.size, self.tSeq, self.qSeq)

    def swapSidesReverseComplement(self, newPsl):
        "construct a block with query and target swapped and reverse complemented "
        return PslBlock(self.psl.tSize - self.tEnd,
                        self.psl.qSize - self.qEnd, self.size,
                        (dnaOps.reverseComplement(self.tSeq) if (self.tSeq is not None) else None),
                        (dnaOps.reverseComplement(self.qSeq) if (self.qSeq is not None) else None))


class Psl(object):
    """Object containing data from a PSL record."""
    __slots__ = ("match", "misMatch", "repMatch", "nCount", "qNumInsert", "qBaseInsert", "tNumInsert", "tBaseInsert", "strand", "qName", "qSize", "qStart", "qEnd", "tName", "tSize", "tStart", "tEnd", "blocks")

    @classmethod
    def _parseBlocks(cls, psl, blockCount, blockSizesStr, qStartsStr, tStartsStr, qSeqsStr, tSeqsStr):
        "convert parallel arrays to PslBlock objects"
        blockSizes = intArraySplit(blockSizesStr)
        qStarts = intArraySplit(qStartsStr)
        tStarts = intArraySplit(tStartsStr)
        haveSeqs = (qSeqsStr is not None)
        if haveSeqs:
            qSeqs = strArraySplit(qSeqsStr)
            tSeqs = strArraySplit(tSeqsStr)
        for i in range(blockCount):
            psl.addBlock(PslBlock(qStarts[i], tStarts[i], blockSizes[i],
                                  (qSeqs[i] if haveSeqs else None),
                                  (tSeqs[i] if haveSeqs else None)))

    def __init__(self, qName=None, qSize=0, qStart=0, qEnd=0,
                 tName=None, tSize=0, tStart=0, tEnd=0,
                 strand=None):
        "create a new PSL with no blocks"
        self.match = 0
        self.misMatch = 0
        self.repMatch = 0
        self.nCount = 0
        self.qNumInsert = 0
        self.qBaseInsert = 0
        self.tNumInsert = 0
        self.tBaseInsert = 0
        self.strand = strand
        self.qName = qName
        self.qSize = qSize
        self.qStart = qStart
        self.qEnd = qEnd
        self.tName = tName
        self.tSize = tSize
        self.tStart = tStart
        self.tEnd = tEnd
        self.blocks = []

    @classmethod
    def fromRow(cls, row):
        """"Create PSL from a text row of columns, usually split from a tab
        file line"""
        psl = Psl(qName=row[9], qSize=int(row[10]), qStart=int(row[11]), qEnd=int(row[12]),
                  tName=row[13], tSize=int(row[14]), tStart=int(row[15]), tEnd=int(row[16]),
                  strand=row[8])
        psl.match = int(row[0])
        psl.misMatch = int(row[1])
        psl.repMatch = int(row[2])
        psl.nCount = int(row[3])
        psl.qNumInsert = int(row[4])
        psl.qBaseInsert = int(row[5])
        psl.tNumInsert = int(row[6])
        psl.tBaseInsert = int(row[7])
        blockCount = int(row[17])
        haveSeqs = len(row) > 21
        cls._parseBlocks(psl, blockCount, row[18], row[19], row[20],
                         (row[21] if haveSeqs else None),
                         (row[22] if haveSeqs else None))
        return psl

    @classmethod
    def fromDbRow(cls, row, dbColIdxMap):
        """"Create PSL from a database row"""
        # FIXME: change to use DictCursor
        psl = Psl(qName=row[dbColIdxMap["qName"]],
                  qSize=row[dbColIdxMap["qSize"]],
                  qStart=row[dbColIdxMap["qStart"]],
                  qEnd=row[dbColIdxMap["qEnd"]],
                  tName=row[dbColIdxMap["tName"]],
                  tSize=row[dbColIdxMap["tSize"]],
                  tStart=row[dbColIdxMap["tStart"]],
                  tEnd=row[dbColIdxMap["tEnd"]],
                  strand=row[dbColIdxMap["strand"]],)
        psl.match = row[dbColIdxMap["matches"]]
        psl.misMatch = row[dbColIdxMap["misMatches"]]
        psl.repMatch = row[dbColIdxMap["repMatches"]]
        psl.nCount = row[dbColIdxMap["nCount"]]
        psl.qNumInsert = row[dbColIdxMap["qNumInsert"]]
        psl.qBaseInsert = row[dbColIdxMap["qBaseInsert"]]
        psl.tNumInsert = row[dbColIdxMap["tNumInsert"]]
        psl.tBaseInsert = row[dbColIdxMap["tBaseInsert"]]
        blockCount = row[dbColIdxMap["blockCount"]]
        haveSeqs = "qSeqs" in dbColIdxMap
        cls._parseBlocks(psl, blockCount, row[dbColIdxMap["blockSizes"]],
                         row[dbColIdxMap["qStarts"]], row[dbColIdxMap["tStarts"]],
                         (row[dbColIdxMap["qSeqs"]] if haveSeqs else None),
                         (row[dbColIdxMap["tSeqs"]] if haveSeqs else None))
        return psl

    @classmethod
    def create(cls,
               qName=None, qSize=0, qStart=0, qEnd=0,
               tName=None, tSize=0, tStart=0, tEnd=0,
               strand=None):
        "create a new PSL"
        psl = Psl(qName=qName, qSize=qSize, qStart=qStart, qEnd=qEnd,
                  tName=tName, tSize=tSize, tStart=tStart, tEnd=tEnd,
                  strand=strand)
        return psl

    def addBlock(self, blk):
        blk.psl = self
        blk.iBlk = len(self.blocks)
        self.blocks.append(blk)

    @property
    def blockCount(self):
        return len(self.blocks)

    @property
    def qStrand(self):
        return self.strand[0]

    @property
    def tStrand(self):
        return (self.strand[1] if len(self.strand) > 1 else "+")

    @deprecated()
    def getQStrand(self):
        return self.qStrand

    @deprecated()
    def getTStrand(self):
        return self.tStrand

    @deprecated()
    def qRevRange(self, start, end):
        "reverse a query range to the other strand (dropping, this is dumb)"
        return (self.qSize - end, self.qSize - start)

    @deprecated()
    def tRevRange(self, start, end):
        "reverse a query range to the other strand (dropping, this is dumb)"
        return (self.tSize - end, self.tSize - start)

    @deprecated()
    def qRangeToPos(self, start, end):
        "convert a query range in alignment coordinates to positive strand coordinates"
        if self.qStrand == "+":
            return (start, end)
        else:
            return (self.qSize - end, self.qSize - start)

    @deprecated()
    def tRangeToPos(self, start, end):
        "convert a target range in alignment coordinates to positive strand coordinates"
        if self.tStrand == "+":
            return (start, end)
        else:
            return (self.tSize - end, self.tSize - start)

    def isProtein(self):
        lastBlock = self.blockCount - 1
        if len(self.strand) < 2:
            return False
        return (((self.strand[1] == '+') and
                 (self.tEnd == self.tStarts[lastBlock] + 3 * self.blockSizes[lastBlock]))
                or
                ((self.strand[1] == '-') and
                 (self.tStart == (self.tSize - (self.tStarts[lastBlock] + 3 * self.blockSizes[lastBlock])))))

    @property
    def tLength(self):
        return self.tEnd - self.tStart

    @property
    def qLength(self):
        return self.qEnd - self.qStart

    def tOverlap(self, tName, tStart, tEnd):
        "test for overlap of target range"
        return (tName == self.tName) and (tStart < self.tEnd) and (tEnd > self.tStart)

    def tBlkOverlap(self, tStart, tEnd, iBlk):
        "does the specified block overlap the target range"
        return (tStart < self.getTEndPos(iBlk)) and (tEnd > self.getTStartPos(iBlk))

    def toRow(self):
        "convert PSL to array of strings"
        row = [str(self.match),
               str(self.misMatch),
               str(self.repMatch),
               str(self.nCount),
               str(self.qNumInsert),
               str(self.qBaseInsert),
               str(self.tNumInsert),
               str(self.tBaseInsert),
               self.strand,
               self.qName,
               str(self.qSize),
               str(self.qStart),
               str(self.qEnd),
               self.tName,
               str(self.tSize),
               str(self.tStart),
               str(self.tEnd),
               str(self.blockCount),
               intArrayJoin([b.size for b in self.blocks]),
               intArrayJoin([b.qStart for b in self.blocks]),
               intArrayJoin([b.tStart for b in self.blocks])]
        if self.blocks[0].qSeq is not None:
            row.append(strArrayJoin([b.qSeq for b in self.blocks]))
            row.append(strArrayJoin([b.tSeq for b in self.blocks]))
        return row

    def __str__(self):
        "return psl as a tab-separated string"
        return "\t".join(self.toRow())

    def write(self, fh):
        """write psl to a tab-seperated file"""
        fh.write(str(self))
        fh.write('\n')

    @staticmethod
    def queryKey(psl):
        "sort key using query address"
        return (psl.qName, psl.qStart, psl.qEnd)

    @staticmethod
    def targetKey(psl):
        "sort key using target address"
        return (psl.tName, psl.tStart, psl.tEnd)

    def __eq__(self, other):
        "compare for equality of alignment"
        if ((not isinstance(other, self.__class__))
            or (self.match != other.match)
            or (self.misMatch != other.misMatch)
            or (self.repMatch != other.repMatch)
            or (self.nCount != other.nCount)
            or (self.qNumInsert != other.qNumInsert)
            or (self.qBaseInsert != other.qBaseInsert)
            or (self.tNumInsert != other.tNumInsert)
            or (self.tBaseInsert != other.tBaseInsert)
            or (self.strand != other.strand)
            or (self.qName != other.qName)
            or (self.qSize != other.qSize)
            or (self.qStart != other.qStart)
            or (self.qEnd != other.qEnd)
            or (self.tName != other.tName)
            or (self.tSize != other.tSize)
            or (self.tStart != other.tStart)
            or (self.tEnd != other.tEnd)
            or (self.blockCount != other.blockCount)):
            return False
        for i in range(self.blockCount):
            if not self.blocks[i].sameAlign(other.blocks[i]):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def sameAlign(self, other):
        "compare for equality of alignment.  The stats fields are not compared."
        if ((other is None)
            or (self.strand != other.strand)
            or (self.qName != other.qName)
            or (self.qSize != other.qSize)
            or (self.qStart != other.qStart)
            or (self.qEnd != other.qEnd)
            or (self.tName != other.tName)
            or (self.tSize != other.tSize)
            or (self.tStart != other.tStart)
            or (self.tEnd != other.tEnd)
            or (self.blockCount != other.blockCount)):
            return False
        for i in range(self.blockCount):
            if not self.blocks[i].sameAlign(other.blocks[i]):
                return False
        return True

    def __hash__(self):
        return hash(self.tName) + hash(self.tStart)

    def identity(self):
        # FIXME: make property
        aligned = float(self.match + self.misMatch + self.repMatch)
        if aligned == 0.0:
            return 0.0  # just matches Ns
        else:
            return (self.match + self.repMatch) / aligned

    def basesAligned(self):
        # FIXME: make property
        return self.match + self.misMatch + self.repMatch

    def queryAligned(self):
        # FIXME: make property
        return (self.match + self.misMatch + self.repMatch) / self.qSize

    def reverseComplement(self):
        "create a new PSL that is reverse complemented"
        rc = Psl(qName=self.qName, qSize=self.qSize, qStart=self.qStart, qEnd=self.qEnd,
                 tName=self.tName, tSize=self.tSize, tStart=self.tStart, tEnd=self.tEnd,
                 strand=reverseStrand(self.qStrand) + reverseStrand(self.tStrand))
        rc.match = self.match
        rc.misMatch = self.misMatch
        rc.repMatch = self.repMatch
        rc.nCount = self.nCount
        rc.qNumInsert = self.qNumInsert
        rc.qBaseInsert = self.qBaseInsert
        rc.tNumInsert = self.tNumInsert
        rc.tBaseInsert = self.tBaseInsert
        for i in range(self.blockCount - 1, -1, -1):
            rc.addBlock(self.blocks[i].reverseComplement(rc))
        return rc

    def _swapStrand(self, keepTStrandImplicit, doRc):
        # don't make implicit if already explicit
        if keepTStrandImplicit and (len(self.strand) == 1):
            qs = reverseStrand(self.tStrand) if doRc else self.tStrand
            ts = ""
        else:
            # swap and make|keep explicit
            qs = self.tStrand
            ts = self.qStrand
        return qs + ts

    def swapSides(self, keepTStrandImplicit=False):
        """Create a new PSL with target and query swapped,

        If keepTStrandImplicit is True the psl has an implicit positive target strand, reverse
        complement to keep the target strand positive and implicit.

        If keepTStrandImplicit is False, don't reverse complement untranslated
        alignments to keep target positive strand.  This will make the target
        strand explicit."""
        doRc = (keepTStrandImplicit and (len(self.strand) == 1) and (self.qStrand == "-"))

        swap = Psl(qName=self.tName, qSize=self.tSize,
                   qStart=self.tStart, qEnd=self.tEnd,
                   tName=self.qName, tSize=self.qSize,
                   tStart=self.qStart, tEnd=self.qEnd,
                   strand=self._swapStrand(keepTStrandImplicit, doRc))
        swap.match = self.match
        swap.misMatch = self.misMatch
        swap.repMatch = self.repMatch
        swap.nCount = self.nCount
        swap.qNumInsert = self.tNumInsert
        swap.qBaseInsert = self.tBaseInsert
        swap.tNumInsert = self.qNumInsert
        swap.tBaseInsert = self.qBaseInsert

        if doRc:
            for i in range(self.blockCount - 1, -1, -1):
                swap.addBlock(self.blocks[i].swapSidesReverseComplement(swap))
        else:
            for i in range(self.blockCount):
                swap.addBlock(self.blocks[i].swapSides(swap))
        return swap


class PslReader(object):
    """Generator to read PSLs from a tab file or file-like object"""
    def __init__(self, fspec):
        self.fspec = fspec

    def __iter__(self):
        for psl in TabFileReader(self.fspec, rowClass=Psl.fromRow, hashAreComments=True, skipBlankLines=True):
            yield psl


class PslTbl(list):
    """Table of PSL objects loaded from a tab-file
    """

    def __init__(self, fileName, qNameIdx=False, tNameIdx=False, qUniqDrop=False):
        for psl in PslReader(fileName):
            self.append(psl)
        self.qNameMap = self.tNameMap = None
        if qNameIdx:
            self._mkQNameIdx(qUniqDrop)
        if tNameIdx:
            self._mkTNameIdx()

    def _mkQNameIdx(self, qUniqDrop):
        self.qNameMap = defaultdict(list)
        for psl in self:
            n = dropQueryUniq(psl.qName) if qUniqDrop else psl.qName
            self.qNameMap[n].append(psl)

    def _mkTNameIdx(self):
        self.tNameMap = defaultdict(list)
        for psl in self:
            self.tNameMap[psl.tName](psl)
        self.tNameMap.default_factory = None

    def getQNames(self):
        return list(self.qNameMap.keys())

    def haveQName(self, qName):
        return (self.qNameMap.get(qName) is not None)

    def genByQName(self, qName):
        """generator to get PSL for a give qName"""
        ent = self.qNameMap.get(qName)
        if ent is not None:
            for psl in ent:
                yield psl

    def getByQName(self, qName):
        """get list of PSLs for a give qName"""
        return list(self.genByQName(qName))

    def getTNames(self):
        return list(self.tNameMap.keys())

    def haveTName(self, tName):
        return (self.tNameMap.get(tName) is not None)

    def genByTName(self, tName):
        """generator to get PSL for a give tName"""
        ent = self.tNameMap.get(tName)
        if ent is not None:
            for psl in ent:
                yield psl

    def getByTName(self, tName):
        """get a list PSL for a give tName"""
        return list(self.genByTName(tName))


def pslFromExonerateCigar(qName, qSize, qStart, qEnd, qStrand, tName, tSize, tStart, tEnd, tStrand, cigarStr):
    "create a PSL from an Ensembl-style cigar formatted alignment"
    def processMatch(psl, size, qNext, tNext):
        psl.addBlock(PslBlock(qNext, tNext, size))
        psl.match += size
        return (qNext + size, tNext + size)

    def processInsert(psl, size, tNext):
        psl.tNumInsert += 1
        psl.tBaseInsert += size
        return tNext + size

    def processDelete(psl, size, qNext):
        psl.qNumInsert += 1
        psl.qBaseInsert += size
        return qNext + size

    cigar = ExonerateCigar(cigarStr)
    psl = Psl.create(qName=qName, qSize=qSize, qStart=qStart, qEnd=qEnd,
                     tName=tName, tSize=tSize, tStart=tStart, tEnd=tEnd,
                     strand=qStrand + tStrand)

    qNext = qStart
    qBlkEnd = qEnd
    if qStrand == '-':
        qNext, qBlkEnd = reverseCoords(qNext, qBlkEnd, qSize)
    tNext = tStart
    tBlkEnd = tEnd
    if tStrand == '-':
        tNext, tBlkEnd = reverseCoords(tNext, tBlkEnd, tSize)

    for op in cigar:
        if op.aligned:
            qNext, tNext = processMatch(psl, op.count, qNext, tNext)
        elif op.tinsert:
            tNext = processInsert(psl, op.count, tNext)
        elif op.tdelete:
            qNext = processDelete(psl, op.count, qNext)
        else:
            raise Exception("invalid CIGAR op {} in {}".format(op, cigar))

    if qNext != qBlkEnd:
        raise Exception("CIGAR length does not match aligned query range: {} {}".format(qName, cigar))
    if tNext != tBlkEnd:
        raise Exception("CIGAR length does not match aligned target range: {} {}".format(qName, cigar))
    if psl.tStrand == '-':
        psl = psl.reverseComplement()
    psl.strand = psl.strand[0]   # BLAT convention
    return psl
