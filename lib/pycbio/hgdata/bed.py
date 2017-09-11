# Copyright 2006-2012 Mark Diekhans
from pycbio.tsv.tabFile import TabFile, TabFileReader
from pycbio.hgdata.autoSql import intArraySplit, intArrayJoin
from collections import defaultdict, namedtuple


# FIXME: not complete, needs tests

class Bed(object):
    """Object wrapper for a BED record"""
    __slots__ = ("chrom", "chromStart", "chromEnd", "name", "score",
                 "strand", "thickStart", "thickEnd", "itemRgb", "blocks")

    class Block(namedtuple("Block", ("start", "end"))):
        """A block in the BED.  Coordinates are absolute, not relative"""
        __slots__ = ()

        def __len__(self):
            return self.end - self.start

    def __init__(self, chrom, chromStart, chromEnd, name=None, score=None, strand=None,
                 thickStart=None, thickEnd=None, itemRgb=None, blocks=None):
        self.chrom = chrom
        self.chromStart = chromStart
        self.chromEnd = chromEnd
        self.name = name
        self.score = score
        self.strand = strand
        self.thickStart = thickStart
        self.thickEnd = thickEnd
        self.itemRgb = itemRgb
        self.blocks = blocks

    @property
    def numCols(self):
        "Returns the number of columns in the BED"
        for i in xrange(len(self.__slots__)):
            if getattr(self, self.__slots__[i]) is None:
                break
        if i == 9:
            i = 11  # blocks take up three columns
        return i

    def __getBlockColumns(self):
        relStarts = []
        sizes = []
        for blk in self.blocks:
            relStarts.append(str(blk.start - self.chromStart))
            sizes.append(str(len(blk)))
        return [intArrayJoin(sizes), intArrayJoin(relStarts)]

    def getRow(self):
        numCols = self.numCols
        row = [self.chrom, str(self.chromStart), str(self.chromEnd)]
        if numCols > 3:
            row.append(str(self.name))
        if numCols > 4:
            row.append(str(self.score))
        if numCols > 5:
            row.append(self.strand)
        if numCols > 7:
            row.append(str(self.thickStart))
            row.append(str(self.thickEnd))
        if numCols > 9:
            row.append(str(self.itemRgb))
        if numCols > 10:
            row.append(str(len(self.blocks)))
            row.extend(self.__getBlockColumns())
        return row

    @staticmethod
    def __parseBlockColumns(chromStart, row):
        sizes = intArraySplit(row[10])
        relStarts = intArraySplit(row[11])
        blocks = []
        for i in xrange(len(relStarts)):
            start = chromStart + relStarts[i]
            blocks.append(Bed.Block(start, start + sizes[i]))
        return blocks

    @staticmethod
    def parse(row):
        """parse bed string columns into a bed object"""
        numCols = len(row)
        chrom = row[0]
        chromStart = int(row[1])
        chromEnd = int(row[2])
        if numCols > 3:
            name = row[3]
        else:
            name = None
        if numCols > 4:
            score = int(row[4])
        else:
            score = None
        if numCols > 5:
            strand = row[5]
        else:
            strand = None
        if numCols > 7:
            thickStart = int(row[6])
            thickEnd = int(row[7])
        else:
            thickStart = None
            thickEnd = None
        if numCols > 8:
            itemRgb = row[8]
        else:
            itemRgb = None
        if numCols > 11:
            blocks = Bed.__parseBlockColumns(chromStart, row)
        else:
            blocks = None
        return Bed(chrom, chromStart, chromEnd, name, score, strand,
                   thickStart, thickEnd, itemRgb, blocks)

    def __str__(self):
        "return BED as a tab-separated string"
        return str.join("\t", self.getRow())

    def write(self, fh):
        """write BED to a tab-seperated file"""
        fh.write(str(self))
        fh.write('\n')


class BedReader(TabFileReader):
    """Reader for BED objects loaded from a tab-file"""

    def __init__(self, fileName):
        TabFileReader.__init__(self, fileName, rowClass=Bed, hashAreComments=True, skipBlankLines=True)


class BedTable(TabFile):
    """Table of BED objects loaded from a tab-file
    """

    def __mkNameIdx(self):
        self.nameMap = defaultdict(list)
        for bed in self:
            self.nameMap[bed.name].append(bed)

    def __init__(self, fileName, nameIdx=False):
        TabFile.__init__(self, fileName, rowClass=lambda r: Bed.parse(r), hashAreComments=True)
        self.nameMap = None
        if nameIdx:
            self.__mkNameIdx()

    def getByName(self, name):
        "get *tuple* of BEDs by name"
        if name in self.nameMap:
            return tuple(self.nameMap[name])
        else:
            return ()
