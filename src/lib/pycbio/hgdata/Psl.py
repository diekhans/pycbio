import copy
from pycbio.tsv.TabFile import TabFile
from pycbio.hgdata.AutoSql import intArraySplit, intArrayJoin, strArraySplit, strArrayJoin
from pycbio.sys import fileOps
from pycbio.sys.MultiDict import MultiDict
from Bio.Seq import reverse_complement

# FIXME: create a block object, build on TSV

class Psl(object):
    """Object wrapper for a parsing a PSL record"""

    def _parse(self, row):
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
        self.blockSizes = intArraySplit(row[18])
        self.qStarts = intArraySplit(row[19])
        self.tStarts = intArraySplit(row[20])
        if len(row) > 21:
            self.qSeqs = strArraySplit(row[21])
            self.tSeqs = strArraySplit(row[22])
        else:
            self.qSeqs = None
            self.tSeqs = None

    def _empty(self, row):
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
        self.blockSizes = None
        self.qStarts = []
        self.tStarts = []
        self.qSeqs = None
        self.tSeqs = None

    def __init__(self, row=None):
        "construct a new PSL, either parsing a row, or creating an empty one"
        if row != None:
            self._parse(row)
        else:
            self._empty()

    def getQEnd(self, iBlk):
        "compute qEnd for a block"
        return self.qStarts[iBlk]+self.blockSizes[iBlk]

    def getTEnd(self, iBlk):
        "compute tEnd for a block"
        return self.tStarts[iBlk]+self.blockSizes[iBlk]

    def getQStrand(self):
        return self.strand[0]

    def getTStrand(self):
        return (self.strand[1] if len(self.strand) > 1 else "+")

    def getQStartPos(self, iBlk):
        "get qStart for a block on positive strand"
        if self.strand[0] == '+':
            return self.qStarts[iBlk]
        else:
            return self.qSize - (self.qStarts[iBlk]+self.blockSizes[iBlk])

    def getQEndPos(self, iBlk):
        "get qEnd for a block on positive strand"
        if self.strand[0] == '+':
            return self.qStarts[iBlk]+self.blockSizes[iBlk]
        else:
            return self.qSize - self.qStarts[iBlk]

    def getTStartPos(self, iBlk):
        "get tStart for a block on positive strand"
        if self.getTStrand() == '+':
            return self.tStarts[iBlk]
        else:
            return self.tSize - (self.tStarts[iBlk]+self.blockSizes[iBlk])

    def getTEndPos(self, iBlk):
        "get tEnd for a block on positive strand"
        if self.getTStrand() == '+':
            return self.tStarts[iblk]+self.blockSizes[iBlk]
        else:
            return self.tSize - self.tStarts[iBlk]

    def isProtein(self):
        lastBlock = self.blockCount - 1
        if len(self.strand) < 2:
            return False
        return (((self.strand[1] == '+' ) and
                 (self.tEnd == self.tStarts[lastBlock] + 3*self.blockSizes[lastBlock]))
                or
                ((self.strand[1] == '-') and
                 (self.tStart == (self.tSize-(self.tStarts[lastBlock] + 3*self.blockSizes[lastBlock])))))

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
               intArrayJoin(self.blockSizes),
               intArrayJoin(self.qStarts),
               intArrayJoin(self.tStarts)]
        if self.qSeqs != None:
            row.append(strArrayJoin(self.qSeqs))
            row.append(strArrayJoin(self.tSeqs))
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
                cmp = psl1.qEmd - psl2.qEnd
        return cmp

    def targetCmp(psl1, psl2):
        "sort compairson using target address"
        cmp = string.cmp(psl1.tName, psl2.tName)
        if cmp != 0:
            cmp = psl1.tStart - psl2.tStart
            if cmp != 0:
                cmp = psl1.tEmd - psl2.tEnd
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
            if ((self.blockSizes[i] != other.blockSizes[i])
                or (self.qStarts[i] != other.qStarts[i])
                or (self.tStarts[i] != other.tStarts[i])):
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
        rc = copy.deepcopy(self)
        rc.strand = ('-' if self.strand[0] != '+' else '+') \
                    + ('-' if (len(self.strand) < 2) or (self.strand[1] != '+') else '+')
        j = 0
        for i in xrange(self.blockCount-1,-1,-1):
            bs = self.blockSizes[i]
            rc.qStarts[j] = (self.qSize - (self.qStarts[i]+bs))
            rc.tStarts[j] = (self.tSize - (self.tStarts[i]+bs))
            rc.blockSizes[j] = bs
            if self.qSeqs != None:
                rc.qSeqs[j] = reverse_complement(self.qSeqs[i])
                rc.tSeqs[j] = reverse_complement(self.tSeqs[i])
            j += 1
        return rc

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

    def _mkQNameIdx(self):
        self.qNameMap = MultiDict()
        for psl in self:
            self.qNameMap.add(psl.qName, psl)

    def __init__(self, fileName, qNameIdx=False):
        TabFile.__init__(self, fileName, rowClass=Psl, hashAreComments=True)
        self.qNameMap = None
        if qNameIdx:
            self._mkQNameIdx()

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
