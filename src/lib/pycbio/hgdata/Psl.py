from pycbio.tsv.TabFile import TabFile
from pycbio.hgdata.AutoSql import intArraySplit, intArrayJoin

# FIXME: create a block object, build on TSV

class Psl(object):
    """Object wrapper for a parsing a PSL record"""

    def __init__(self, row):
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

    def __eq__(self, other):
        "compare for equality of alignment.  The stats fields are not compared."
        if ((self.strand != other.strand)
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

    def covered(self):
        return self.match + self.misMatch + self.repMatch

    def covereage(self):
        return float(self.match + self.misMatch + self.repMatch)/float(self.qSize)

class PslTbl(TabFile):
    """Table of PSL objects loaded from a tab-file
    """

    def _mkQNameIdx(self):
        self.qNameMap = {}
        # single occurances are store directly in map, multiple are saved as
        # list in the map
        for psl in self:
            ent = self.qNameMap.get(psl.qName)
            if ent != None:
                if ent.__class__ is list:
                    ent.append(psl)
                else:
                    # convert entry to list
                    self.qNameMap[psl.qName] = [ent, psl]  

            else:
                self.qNameMap[psl.qName] = psl

    def __init__(self, fileName, qNameIdx=False):
        TabFile.__init__(self, fileName, rowClass=Psl)
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

    def getQNameList(self, qName):
        """get a list of PSL for qName"""
        ent = self.qNameMap.get(qName)
        if ent != None:
            if not isinstance(ent, list):
                ent = [ent]
        return ent

    def havePsl(self, psl):
        "determine if the specified psl is already in the table (by comparison, not object id)"
        for p in self.getByQName(psl.qName):
            if p == psl:
                return True
        return False
