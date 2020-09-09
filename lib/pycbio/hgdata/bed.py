# Copyright 2006-2012 Mark Diekhans
from __future__ import print_function
from builtins import range
import copy
from pycbio.sys import PycbioException
from pycbio.tsv.tabFile import TabFile, TabFileReader
from pycbio.hgdata.autoSql import intArraySplit, intArrayJoin
from collections import defaultdict, namedtuple


# FIXME: not complete, needs tests
# FIXME: really need a better way to deal with derived classes than extraArgs

class Bed(object):
    """Object wrapper for a BED record.  ExtraCols is a vector of extra
    columns to add.  Special columns be added by extending and overriding
    parse() and toRow() to do special handling.  For BED with more than
    specified numbed of parse columns, extra columns as passed though.
    """
    __slots__ = ("chrom", "chromStart", "chromEnd", "name", "score",
                 "strand", "thickStart", "thickEnd", "itemRgb", "blocks",
                 "extraCols")

    class Block(namedtuple("Block", ("start", "end"))):
        """A block in the BED.  Coordinates are absolute, not relative and are transformed on write.
        """
        __slots__ = ()

        def __len__(self):
            return self.end - self.start

        def __str__(self):
            return "{}-{}".format(self.start, self.end)

    def __init__(self, chrom, chromStart, chromEnd, name=None, score=None, strand=None,
                 thickStart=None, thickEnd=None, itemRgb=None, blocks=None, extraCols=None):
        self.chrom = chrom
        self.chromStart = chromStart
        self.chromEnd = chromEnd
        self.name = name
        self.score = score
        self.strand = strand
        self.thickStart = thickStart
        self.thickEnd = thickEnd
        self.itemRgb = itemRgb
        self.blocks = copy.copy(blocks)
        self.extraCols = copy.copy(extraCols)

    @property
    def numberOfColumns(self):
        """Returns the number of columns in the BED when formatted as a row."""
        # exclude extraCols
        for i in range(len(self.__slots__) - 1):
            if getattr(self, self.__slots__[i]) is None:
                break
        if i >= 9:
            i += 2  # blocks take up three columns
        if self.extraCols is not None:
            i += len(self.extraCols)
        return i

    def _getBlockColumns(self):
        relStarts = []
        sizes = []
        for blk in self.blocks:
            relStarts.append(str(blk.start - self.chromStart))
            sizes.append(str(len(blk)))
        return [intArrayJoin(sizes), intArrayJoin(relStarts)]

    def toRow(self):
        row = [self.chrom, str(self.chromStart), str(self.chromEnd)]
        if self.name is not None:
            row.append(str(self.name))
        if self.score is not None:
            row.append(str(self.score))
        if self.strand is not None:
            row.append(self.strand)
        if self.thickStart is not None:
            row.append(str(self.thickStart))
            row.append(str(self.thickEnd))
        if self.itemRgb is not None:
            row.append(str(self.itemRgb))
        if self.blocks is not None:
            row.append(str(len(self.blocks)))
            row.extend(self._getBlockColumns())
        if self.extraCols is not None:
            row.extend([str(c) for c in self.extraCols])
        return row

    @staticmethod
    def _parseBlockColumns(chromStart, row):
        sizes = intArraySplit(row[10])
        relStarts = intArraySplit(row[11])
        blocks = []
        for i in range(len(relStarts)):
            start = chromStart + relStarts[i]
            blocks.append(Bed.Block(start, start + sizes[i]))
        return blocks

    @classmethod
    def parse(cls, row, numStdCols=None):
        """Parse bed string columns into a bed object.  If numStdCols
        is specified, only those columns are parse and the remained goes
        to extraCols."""
        assert((numStdCols is None) or (3 <= numStdCols <= 12))
        if numStdCols is None:
            numStdCols = min(len(row), 12)
        if len(row) < numStdCols:
            raise PycbioException("expected at least {} columns, found {}: ".format(numStdCols, len(row)))
        chrom = row[0]
        chromStart = int(row[1])
        chromEnd = int(row[2])
        if numStdCols > 3:
            name = row[3]
        else:
            name = None
        if numStdCols > 4:
            score = int(row[4])
        else:
            score = None
        if numStdCols > 5:
            strand = row[5]
        else:
            strand = None
        if numStdCols > 7:
            thickStart = int(row[6])
            thickEnd = int(row[7])
        else:
            thickStart = None
            thickEnd = None
        if numStdCols > 8:
            itemRgb = row[8]
        else:
            itemRgb = None
        if numStdCols > 11:
            blocks = Bed._parseBlockColumns(chromStart, row)
        else:
            blocks = None
        if len(row) > numStdCols:
            extraCols = row[numStdCols:]
        else:
            extraCols = None
        return cls(chrom, chromStart, chromEnd, name, score, strand,
                   thickStart, thickEnd, itemRgb, blocks, extraCols)

    def __str__(self):
        "return BED as a tab-separated string"
        return "\t".join(self.toRow())

    @property
    def start(self):
        """alias for chromStart"""
        return self.chromStart

    @property
    def end(self):
        """alias for chromEnd"""
        return self.chromEnd

    @property
    def blockCount(self):
        return len(self.blocks)

    @property
    def span(self):
        "distance from start to end"
        return self.chromEnd - self.chromStart

    @property
    def coverage(self):
        """number of bases covered"""
        if self.blocks is None:
            return self.span()
        else:
            return sum([len(b) for b in self.blocks])

    def write(self, fh):
        """write BED to a tab-separated file"""
        fh.write(str(self))
        fh.write('\n')


def BedReader(fspec, numStdCols=None, bedClass=Bed):
    """Generator to read BED objects loaded from a tab-file or file-like
    object.  See Bed.parse()."""
    for bed in TabFileReader(fspec, rowClass=lambda r: bedClass.parse(r, numStdCols=numStdCols),
                             hashAreComments=True, skipBlankLines=True):
        yield bed


class BedTable(TabFile):
    """Table of BED objects loaded from a tab-file
    """

    def _mkNameIdx(self):
        self.nameMap = defaultdict(list)
        for bed in self:
            self.nameMap[bed.name].append(bed)

    def __init__(self, fileName, nameIdx=False, numStdCols=None):
        super(BedTable, self).__init__(fileName, rowClass=lambda r: Bed.parse(r, numStdCols=numStdCols),
                                       hashAreComments=True, skipBlankLines=True)
        self.nameMap = None
        if nameIdx:
            self._mkNameIdx()

    def getByName(self, name):
        "get *tuple* of BEDs by name"
        if name in self.nameMap:
            return tuple(self.nameMap[name])
        else:
            return ()
