from pycbio.tsv.TabFile import TabFile
from pycbio.hgdata.AutoSql import intArraySplit, intArrayJoin

# FIXME: create a block object, build on TSV

# FIXME: not complete

class Bed(object):
    """Object wrapper for a parsing a BED record"""

    class Block(object):
        def __init__(self, relStart, size):
            self.relStart = relStart
            self.size = size

    def __init__(self, row):
        self.numCols = len(row)
        self.chrom = row[0]
        self.chromStart = int(row[1])
        self.chromEnd = int(row[2])
        self.name = row[3]
        if self.numCols > 4:
            self.score = int(row[4])
        else:
            self.score = None
        if self.numCols > 5:
            self.strand = row[5]
        else:
            self.strand = None
        if self.numCols > 7:
            self.thickStart = int(row[6])
            self.thickEnd = int(row[7])
        else:
            self.thickStart = None
            self.thickEnd = None
            
        if self.numCols > 8:
            self.itemRgb = int(row[8])
        else:
            self.itemRgb = None
        if self.numCols > 11:
            relStarts = intArraySplit(row[10])
            sizes = intArraySplit(row[11])
            self.blocks = []
            for i in xrange(len(relStarts)):
                self.blocks.append(Bed.Block(relStarts[i], sizes[i]))
        else:
            self.blocks = None

    def __str__(self):
        "return BED as a tab-separated string"
        row = [self.chrom, str(self.chromStart), str(self.chromEnd), self.name]
        if self.numCols > 4:
            row.append(str(self.score));
        if self.numCols > 5:
            row.append(self.strand)
        if self.numCols > 7:
            row.append(str(self.thickStart))
            row.append(str(self.thickEnd))
        if self.numCols > 8:
            row.append(str(self.itemRgb))
        if self.numCols > 11:
            row.append(str(len(self.blocks)))
            relStarts = []
            sizes = []
            for blk in self.blocks:
                relStarts.append(str(blk.relStart))
                sizes.append(str(blk.size))
            row.append(intArrayJoin(self.relStart))
            row.append(intArrayJoin(self.sizes))
        return str.join("\t", row)
        
    def write(self, fh):
        """write psl to a tab-seperated file"""
        fh.write(str(self))
        fh.write('\n')        


class BedTbl(TabFile):
    """Table of BED objects loaded from a tab-file
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
