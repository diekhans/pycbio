import copy
from pycbio.tsv.TabFile import TabFile
from pycbio.hgdata.AutoSql import intArraySplit, intArrayJoin, strArraySplit, strArrayJoin
from pycbio.sys import fileOps
from pycbio.sys.MultiDict import MultiDict
from Bio.Seq import reverse_complement

# FIXME: create a block object, build on TSV

def rcStrand(s):
    "return reverse-complement of a strand character"
    return "+" if (s == "-") else "-"

class PslBlock(object):
    """Block of a PSL"""
    __slots__ = ("psl", "qStart", "qEnd", "tStart", "tEnd", "size", "qSeq", "tSeq")

    def __init__(self, psl, qStart, tStart, size, qSeq=None, tSeq=None):
        self.psl = psl
        self.qStart= qStart
        self.qEnd = qStart + size
        self.tStart = tStart
        self.tEnd = tStart + size
        self.size = size
        self.qSeq = qSeq
        self.tSeq = tSeq

    def __len__(self):
        return self.size

    def getQStartPos(self):
        "get qStart for the block on positive strand"
        if self.psl.getQStrand() == '+':
            return self.qStart
        else:
            return self.psl.qSize - self.qEnd

    def getQEndPos(self):
        "get qEnd for the block on positive strand"
        if self.psl.getQStrand() == '+':
            return self.qEnd
        else:
            return self.psl.qSize - self.qStart

    def getTStartPos(self):
        "get tStart for the block on positive strand"
        if self.psl.getTStrand() == '+':
            return self.tStart
        else:
            return self.psl.tSize - self.tEnd

    def getTEndPos(self):
        "get tEnd for the block on positive strand"
        if self.psl.getTStrand() == '+':
            return self.tEnd
        else:
            return self.psl.tSize - self.tStart

    def sameAlign(self, other):
        "compare for equality of alignment."
        return (other != None) and (self.qStart == other.qStart) and (self.tStart == other.tStart) and (self.size == other.size)

    def reverseComplement(self, newPsl):
        "construct a block that is the reverse complement of this block"
        return PslBlock(newPsl, self.psl.qSize-self.qEnd, self.psl.tSize-self.tEnd, self.size,
                        (reverse_complement(self.qSeq) if (self.qSeq != None) else None),
                        (reverse_complement(self.tSeq) if (self.tSeq != None) else None))

    def swapSides(self, newPsl):
        "construct a block with query and target swapped "
        return PslBlock(newPsl, self.tStart, self.qStart, self.size, self.tSeq, self.qSeq)

    def swapSidesReverseComplement(self, newPsl):
        "construct a block with query and target swapped and reverse complemented "
        return PslBlock(newPsl, self.psl.tSize-self.tEnd, self.psl.qSize-self.qEnd, self.size,
                        (reverse_complement(self.tSeq) if (self.tSeq != None) else None),
                        (reverse_complement(self.qSeq) if (self.qSeq != None) else None))

class Psl(object):
    """Object containing data from a PSL record."""
    __slots__ = ("match", "misMatch", "repMatch", "nCount", "qNumInsert", "qBaseInsert", "tNumInsert", "tBaseInsert", "strand", "qName", "qSize", "qStart", "qEnd", "tName", "tSize", "tStart", "tEnd", "blockCount", "blocks")

    def __parse(self, row):
        self.match = int(row[0])
        self.misMatch = int(row[1])
        self.repMatch = int(row[2])
        self.nCount = int(row[3])
        self.qNumInsert = int(row[4])
        self.qBaseInsert = int(row[5])
        self.tNumInsert = int(row[6])
        self.tBaseInsert = int(row[7])
        self.strand = row[8]
        self.qName = row[9]
        self.qSize = int(row[10])
        self.qStart = int(row[11])
        self.qEnd = int(row[12])
        self.tName = row[13]
        self.tSize = int(row[14])
        self.tStart = int(row[15])
        self.tEnd = int(row[16])
        self.blockCount = int(row[17])
        self.blocks = []

        # convert parallel arrays
        blockSizes = intArraySplit(row[18])
        qStarts = intArraySplit(row[19])
        tStarts = intArraySplit(row[20])
        haveSeqs = len(row) > 21
        if haveSeqs:
            qSeqs = strArraySplit(row[21])
            tSeqs = strArraySplit(row[22])

        for i in xrange(self.blockCount):
            self.blocks.append(PslBlock(self, qStarts[i], tStarts[i], blockSizes[i],
                                        (qSeqs[i] if haveSeqs else None),
                                        (tSeqs[i] if haveSeqs else None)))


    def __empty(self):
        self.match = 0
        self.misMatch = 0
        self.repMatch = 0
        self.nCount = 0
        self.qNumInsert = 0
        self.qBaseInsert = 0
        self.tNumInsert = 0
        self.tBaseInsert = 0
        self.strand = None
        self.qName = None
        self.qSize = 0
        self.qStart = 0
        self.qEnd = 0
        self.tName = None
        self.tSize = 0
        self.tStart = 0
        self.tEnd = 0
        self.blockCount = 0
        self.blocks = []

    def __init__(self, row=None):
        "construct a new PSL, either parsing a row, or creating an empty one"
        if row != None:
            self.__parse(row)
        else:
            self.__empty()

    def getQStrand(self):
        return self.strand[0]

    def getTStrand(self):
        return (self.strand[1] if len(self.strand) > 1 else "+")

    def qRangeToPos(self, start, end):
        "convert a query range in alignment coordinates to positive strand coordinates"
        if self.getQStrand() == "+":
            return (start, end)
        else:
            return (self.qSize-end, self.qSize-start)

    def tRangeToPos(self, start, end):
        "convert a target range in alignment coordinates to positive strand coordinates"
        if self.getTStrand() == "+":
            return (start, end)
        else:
            return (self.tSize-end, self.tSize-start)

    def isProtein(self):
        lastBlock = self.blockCount - 1
        if len(self.strand) < 2:
            return False
        return (((self.strand[1] == '+' ) and
                 (self.tEnd == self.tStarts[lastBlock] + 3*self.blockSizes[lastBlock]))
                or
                ((self.strand[1] == '-') and
                 (self.tStart == (self.tSize-(self.tStarts[lastBlock] + 3*self.blockSizes[lastBlock])))))

    def tOverlap(self, tName, tStart, tEnd):
        "test for overlap of target range"
        return (tName == self.tName) and  (tStart < self.tEnd) and (tEnd > self.tStart)

    def tBlkOverlap(self, tStart, tEnd, iBlk):
        "does the specified block overlap the target range"
        return (tStart < self.getTEndPos(iBlk)) and (tEnd > self.getTStartPos(iBlk))

    def __str__(self):
        "return psl as a tab-separated string"
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
        if self.blocks[0].qSeq != None:
            row.append(strArrayJoin([b.qSeq for b in self.blocks]))
            row.append(strArrayJoin([b.tSeq for b in self.blocks]))
        return str.join("\t", row)
        
    def write(self, fh):
        """write psl to a tab-seperated file"""
        fh.write(str(self))
        fh.write('\n')        

    def queryCmp(psl1, psl2):
        "sort compairson using query address"
        cmp = string.cmp(psl1.qName, psl2.qName)
        if cmp != 0:
            cmp = psl1.qStart - psl2.qStart
            if cmp != 0:
                cmp = psl1.qEnd - psl2.qEnd
        return cmp

    def targetCmp(psl1, psl2):
        "sort compairson using target address"
        cmp = string.cmp(psl1.tName, psl2.tName)
        if cmp != 0:
            cmp = psl1.tStart - psl2.tStart
            if cmp != 0:
                cmp = psl1.tEnd - psl2.tEnd
        return cmp

    def sameAlign(self, other):
        "compare for equality of alignment.  The stats fields are not compared."
        if ((other == None) 
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
        for i in xrange(self.blockCount):
            if not self.blocks[i].sameAlign(other.blocks[i]):
                return False
        return True

    def __hash__(self):
        return hash(self.tName) + hash(self.tStart)

    def identity(self):
        aligned = float(self.match + self.misMatch + self.repMatch)
        if aligned == 0.0:
            return 0.0
        else:
            return float(self.match + self.repMatch)/aligned

    def basesAligned(self):
        return self.match + self.misMatch + self.repMatch

    def queryAligned(self):
        return float(self.match + self.misMatch + self.repMatch)/float(self.qSize)

    def reverseComplement(self):
        "create a new PSL that is reverse complemented"
        rc = Psl(None)
        rc.match = self.match
        rc.misMatch = self.misMatch
        rc.repMatch = self.repMatch
        rc.nCount = self.nCount
        rc.qNumInsert = self.qNumInsert
        rc.qBaseInsert = self.qBaseInsert
        rc.tNumInsert = self.tNumInsert
        rc.tBaseInsert = self.tBaseInsert
        rc.strand = rcStrand(self.getQStrand()) + rcStrand(self.getTStrand())
        rc.qName = self.qName
        rc.qSize = self.qSize
        rc.qStart = self.qStart
        rc.qEnd = self.qEnd
        rc.tName = self.tName
        rc.tSize = self.tSize
        rc.tStart = self.tStart
        rc.tEnd = self.tEnd
        rc.blockCount = self.blockCount
        rc.blocks = []
        for i in xrange(self.blockCount-1,-1,-1):
            rc.blocks.append(self.blocks[i].reverseComplement(rc))
        return rc

    def __swapStrand(self, rc, keepTStrandImplicit, doRc):
        # don't make implicit if already explicit
        if keepTStrandImplicit and (len(self.strand) == 1):
            qs = rcStrand(self.getTStrand()) if doRc else self.getTStrand()
            ts = ""
        else:
            # swap and make|keep explicit
            qs = self.getTStrand()
            ts = self.getQStrand()
        return qs+ts

    def swapSides(self, keepTStrandImplicit=False):
        """Create a new PSL with target and query swapped, 

        If keepTStrandImplicit is True the psl has an implicit positive target strand, reverse
        complement to keep the target strand positive and implicit.

        If keepTStrandImplicit is False, don't reverse complement untranslated
        alignments to keep target positive strand.  This will make the target
        strand explicit."""
        doRc = (keepTStrandImplicit and (len(self.strand) == 1) and (self.getQStrand() == "-"))
        
        swap = Psl(None)
        swap.match = self.match
        swap.misMatch = self.misMatch
        swap.repMatch = self.repMatch
        swap.nCount = self.nCount
        swap.qNumInsert = self.tNumInsert
        swap.qBaseInsert = self.tBaseInsert
        swap.tNumInsert = self.qNumInsert
        swap.tBaseInsert = self.qBaseInsert
        swap.strand = self.__swapStrand(swap, keepTStrandImplicit, doRc)
        swap.qName = self.tName
        swap.qSize = self.tSize
        swap.qStart = self.tStart
        swap.qEnd = self.tEnd
        swap.tName = self.qName
        swap.tSize = self.qSize
        swap.tStart = self.qStart
        swap.tEnd = self.qEnd
        swap.blockCount = self.blockCount
        swap.blocks = []

        if doRc:
            for i in xrange(self.blockCount-1,-1,-1):
                swap.blocks.append(self.blocks[i].swapSidesReverseComplement(swap))
        else:
            for i in xrange(self.blockCount):
                swap.blocks.append(self.blocks[i].swapSides(swap))
        return swap

class PslReader(object):
    """Read PSLs from a tab file"""

    def __init__(self, fileName):
        self.fh = fileOps.opengz(fileName)

    def __iter__(self):
        return self

    def next(self):
        "read next PSL"
        while True:
            line = self.fh.readline()
            if (line == ""):
                self.fh.close();
                raise StopIteration
            if not ((len(line) == 1) or line.startswith('#')):
                line = line[0:-1]  # drop newline
                return Psl(line.split("\t"))

# FIXME: need to unify PslTbl/PslReader (add TabFileReader)

class PslTbl(TabFile):
    """Table of PSL objects loaded from a tab-file
    """

    def __mkQNameIdx(self):
        self.qNameMap = MultiDict()
        for psl in self:
            self.qNameMap.add(psl.qName, psl)

    def __init__(self, fileName, qNameIdx=False):
        TabFile.__init__(self, fileName, rowClass=Psl, hashAreComments=True)
        self.qNameMap = None
        if qNameIdx:
            self.__mkQNameIdx()

    def getQNameIter(self):
        return self.qNameMap.iterkeys()

    def haveQName(self, qName):
        return (self.qNameMap.get(qName) != None)
        
    def getByQName(self, qName):
        """generator to get all PSL with a give qName"""
        ent = self.qNameMap.get(qName)
        if ent != None:
            if isinstance(ent, list):
                for psl in ent:
                    yield psl
            else:
                yield ent

    def havePsl(self, psl):
        "determine if the specified psl is already in the table (by comparison, not object id)"
        for p in self.qNameMap.get(psl.qName):
            if p == psl:
                return True
        return False
