# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.bed import Bed, BedTable, BedReader


class BedGame(Bed):
    "example derived BED4+3 that adds columns"
    __slots__ = ("year", "month", "day")

    def __init__(self, chrom, chromStart, chromEnd, name=None, year=None, month=None, day=None,
                 score=None, strand=None, thickStart=None, thickEnd=None, itemRgb=None, blocks=None,
                 extraCols=None, numStdCols=None):
        assert numStdCols == 4
        super(BedGame, self).__init__(chrom, chromStart, chromEnd, name, numStdCols=4)
        self.year = year
        self.month = month
        self.day = day

    @property
    def numColumns(self):
        return self.numStdCols + 3

    def toRow(self):
        return super(BedGame, self).toRow() + [str(self.year), str(self.month), str(self.day)]

    @classmethod
    def parse(cls, row, numStdCols=4):
        assert numStdCols == 4
        if len(row) != 7:
            raise Exception("Expected 7 columns, got {}: {}".format(len(row), row))
        b = super(BedGame, cls).parse(row[0:4], 4)
        b.year = int(row[4])
        b.month = int(row[5])
        b.day = int(row[6])
        return b

class BedTests(TestCaseBase):
    def testLoadBed(self):
        beds = BedTable(self.getInputFile("fromPslMinTest.bed"), nameIdx=True)
        self.assertEqual(len(beds), 9)
        hits = beds.getByName("NM_000017.1")
        self.assertEqual(len(hits), 1)
        self.assertEqual(str(hits[0]),
                         "chr12	119575618	119589763	NM_000017.1	0	+	119575641	119589204	0	10	69,164,150,112,152,171,138,96,57,712,	0,1163,11123,11493,11974,12417,12670,12957,13277,13433,")

    def testWriteBed(self):
        beds = BedTable(self.getInputFile("fromPslMinTest.bed"))
        outBedFile = self.getOutputFile(".bed")
        with open(outBedFile, "w") as outFh:
            for bed in beds:
                bed.write(outFh)
        self.diffFiles(self.getInputFile("fromPslMinTest.bed"), outBedFile)

    def testBed12Extra(self):
        beds = BedTable(self.getInputFile("bed12extra.bed"))
        outBedFile = self.getOutputFile(".bed")
        with open(outBedFile, "w") as outFh:
            for bed in beds:
                bed.write(outFh)
        self.diffFiles(self.getInputFile("bed12extra.bed"), outBedFile)

    def testBed6Extra(self):
        outBedFile = self.getOutputFile(".bed")
        with open(outBedFile, "w") as outFh:
            for bed in BedReader(self.getInputFile("bed6extra.bed"), numStdCols=6):
                bed.write(outFh)
        self.diffFiles(self.getInputFile("bed6extra.bed"), outBedFile)

    def testBedExtend(self):
        testRow = ["chrZ", "1000", "2000", "fred", "1962", "7", "1"]
        b1 = BedGame.parse(testRow)
        self.assertEqual(b1.name, "fred")
        self.assertEqual(b1.year, 1962)
        self.assertEqual(b1.month, 7)
        self.assertEqual(b1.day, 1)
        outRow = b1.toRow()
        self.assertEqual(testRow, outRow)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(BedTests))
    return ts


if __name__ == '__main__':
    unittest.main()
