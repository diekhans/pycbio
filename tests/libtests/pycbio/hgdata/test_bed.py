# Copyright 2006-2025 Mark Diekhans
import unittest
import os.path as osp
import sys
import pickle
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.bed import Bed, BedBlock, BedTable, BedReader, bedFromPsl, bedMergeBlocks
from pycbio.sys.color import Color
import pipettor

sys.path.insert(0, osp.dirname(__file__))
from test_psl import psPos, psTransPosNeg, splitToPsl

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

    def testBed6ExtraGzip(self):
        inBedGz = self.getOutputFile(".bed.gz")
        pipettor.run(["gzip", "-c", self.getInputFile("bed6extra.bed")], stdout=inBedGz)
        outBedFile = self.getOutputFile(".bed")
        with open(outBedFile, "w") as outFh:
            for bed in BedReader(inBedGz, numStdCols=6):
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

    def testPickle(self):
        beds = BedTable(self.getInputFile("bed12extra.bed"))
        bed0 = beds[0]
        bedp = pickle.loads(pickle.dumps(bed0))
        self.assertEqual(bedp.chrom, bed0.chrom)
        self.assertEqual(bedp.chromStart, bed0.chromStart)
        for b0, bp in zip(bed0.blocks, bedp.blocks):
            self.assertEqual(bp, b0)

    def testDefaultingStdCols(self):
        bed = Bed("chr22", 100, 200, itemRgb=Color.fromRgb8(255, 0, 255))
        self.assertEqual(bed.toRow(), ["chr22", "100", "200", 'chr22:100-200', '0', '+', '200', '200', '255,0,255'])

        bed = Bed("chr22", 100, 200, "Fred", itemRgb="255,0,255", numStdCols=12)
        self.assertEqual(bed.toRow(), ["chr22", "100", "200", "Fred", '0', '+', '200', '200', '255,0,255', '1', '100,', '0,'])

        bed = Bed("chr22", 100, 200, "Barney", itemRgb="255,0,255", numStdCols=12,
                  extraCols=("Star", "Trek"))
        self.assertEqual(bed.toRow(), ["chr22", "100", "200", 'Barney', '0', '+', '200', '200', '255,0,255', '1', '100,', '0,', "Star", "Trek"])

    def testGaps(self):
        beds = BedTable(self.getInputFile("fromPslMinTest.bed"))
        self.assertEqual(beds[0].getGaps(),
                         (BedBlock(119575687, 119576781),
                          BedBlock(119576945, 119586741),
                          BedBlock(119586891, 119587111),
                          BedBlock(119587223, 119587592),
                          BedBlock(119587744, 119588035),
                          BedBlock(119588206, 119588288),
                          BedBlock(119588426, 119588575),
                          BedBlock(119588671, 119588895),
                          BedBlock(119588952, 119589051)))

    def testBedFromPslPos(self):
        bed = bedFromPsl(splitToPsl(psPos))
        self.assertEqual(bed.toRow(),
                         ['chr22', '48109515', '48454184', 'NM_025031.1', '0', '+', '48454184', '48454184', '0', '4', '17,11,12,81,', '0,18,344032,344588,'])

    def testBedFromPslTransPosNeg(self):
        bed = bedFromPsl(splitToPsl(psTransPosNeg))
        self.assertEqual(bed.toRow(),
                         ['chr1', '92653606', '92661065', 'NM_001020776', '0', '-', '92661065', '92661065', '0', '6', '184,164,135,30,84,57,', '0,2564,4322,4572,6836,7402,'])

    def testBedMerge1(self):
        beds = BedTable(self.getInputFile("lncRNA-locus1.bed"))
        mergedBed = bedMergeBlocks("test1", beds)
        self.assertEqual(mergedBed.toRow(),
                         ['chr1', '148682028', '148712560', 'test1', '0', '-', '148712560', '148712560', '0', '5', '151,335,582,854,304,', '0,1264,23019,26177,30228,'])

    def testFixScores(self):
        with open(self.getOutputFile(".bed"), 'w') as fh:
            for bed in BedReader(self.getInputFile("fixscores.bed"), numStdCols=5, fixScores=True):
                bed.write(fh)
        self.diffExpected(".bed")


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(BedTests))
    return ts


if __name__ == '__main__':
    unittest.main()
