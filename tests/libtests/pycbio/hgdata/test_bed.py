# Copyright 2006-2025 Mark Diekhans
import os.path as osp
import sys
import pickle
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
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

def testLoadBed(request):
    beds = BedTable(ts.get_test_input_file(request, "fromPslMinTest.bed"), nameIdx=True)
    assert len(beds) == 9
    hits = beds.getByName("NM_000017.1")
    assert len(hits) == 1
    assert str(hits[0]) == "chr12	119575618	119589763	NM_000017.1	0	+	119575641	119589204	0	10	69,164,150,112,152,171,138,96,57,712,	0,1163,11123,11493,11974,12417,12670,12957,13277,13433,"

def testWriteBed(request):
    beds = BedTable(ts.get_test_input_file(request, "fromPslMinTest.bed"))
    outBedFile = ts.get_test_output_file(request, ".bed")
    with open(outBedFile, "w") as outFh:
        for bed in beds:
            bed.write(outFh)
    ts.diff_test_files(ts.get_test_input_file(request, "fromPslMinTest.bed"), outBedFile)

def testBed12Extra(request):
    beds = BedTable(ts.get_test_input_file(request, "bed12extra.bed"))
    outBedFile = ts.get_test_output_file(request, ".bed")
    with open(outBedFile, "w") as outFh:
        for bed in beds:
            bed.write(outFh)
    ts.diff_test_files(ts.get_test_input_file(request, "bed12extra.bed"), outBedFile)

def testBed6Extra(request):
    outBedFile = ts.get_test_output_file(request, ".bed")
    with open(outBedFile, "w") as outFh:
        for bed in BedReader(ts.get_test_input_file(request, "bed6extra.bed"), numStdCols=6):
            bed.write(outFh)
    ts.diff_test_files(ts.get_test_input_file(request, "bed6extra.bed"), outBedFile)

def testBed6ExtraGzip(request):
    inBedGz = ts.get_test_output_file(request, ".bed.gz")
    pipettor.run(["gzip", "-c", ts.get_test_input_file(request, "bed6extra.bed")], stdout=inBedGz)
    outBedFile = ts.get_test_output_file(request, ".bed")
    with open(outBedFile, "w") as outFh:
        for bed in BedReader(inBedGz, numStdCols=6):
            bed.write(outFh)
    ts.diff_test_files(ts.get_test_input_file(request, "bed6extra.bed"), outBedFile)

def testBedExtend(request):
    testRow = ["chrZ", "1000", "2000", "fred", "1962", "7", "1"]
    b1 = BedGame.parse(testRow)
    assert b1.name == "fred"
    assert b1.year == 1962
    assert b1.month == 7
    assert b1.day == 1
    outRow = b1.toRow()
    assert testRow == outRow

def testPickle(request):
    beds = BedTable(ts.get_test_input_file(request, "bed12extra.bed"))
    bed0 = beds[0]
    bedp = pickle.loads(pickle.dumps(bed0))
    assert bedp.chrom == bed0.chrom
    assert bedp.chromStart == bed0.chromStart
    for b0, bp in zip(bed0.blocks, bedp.blocks):
        assert bp == b0

def testDefaultingStdCols(request):
    bed = Bed("chr22", 100, 200, itemRgb=Color.fromRgb8(255, 0, 255))
    assert bed.toRow() == ["chr22", "100", "200", 'chr22:100-200', '0', '+', '200', '200', '255,0,255']

    bed = Bed("chr22", 100, 200, "Fred", itemRgb="255,0,255", numStdCols=12)
    assert bed.toRow() == ["chr22", "100", "200", "Fred", '0', '+', '200', '200', '255,0,255', '1', '100,', '0,']

    bed = Bed("chr22", 100, 200, "Barney", itemRgb="255,0,255", numStdCols=12,
              extraCols=("Star", "Trek"))
    assert bed.toRow() == ["chr22", "100", "200", 'Barney', '0', '+', '200', '200', '255,0,255', '1', '100,', '0,', "Star", "Trek"]

def testGaps(request):
    beds = BedTable(ts.get_test_input_file(request, "fromPslMinTest.bed"))
    assert beds[0].getGaps() == (BedBlock(119575687, 119576781),
                                 BedBlock(119576945, 119586741),
                                 BedBlock(119586891, 119587111),
                                 BedBlock(119587223, 119587592),
                                 BedBlock(119587744, 119588035),
                                 BedBlock(119588206, 119588288),
                                 BedBlock(119588426, 119588575),
                                 BedBlock(119588671, 119588895),
                                 BedBlock(119588952, 119589051))

def testBedFromPslPos(request):
    bed = bedFromPsl(splitToPsl(psPos))
    assert bed.toRow() == \
        ['chr22', '48109515', '48454184', 'NM_025031.1', '0', '+', '48454184', '48454184', '0', '4', '17,11,12,81,', '0,18,344032,344588,']

def testBedFromPslTransPosNeg(request):
    bed = bedFromPsl(splitToPsl(psTransPosNeg))
    assert bed.toRow() == \
        ['chr1', '92653606', '92661065', 'NM_001020776', '0', '-', '92661065', '92661065', '0', '6', '184,164,135,30,84,57,', '0,2564,4322,4572,6836,7402,']

def testBedMerge1(request):
    beds = BedTable(ts.get_test_input_file(request, "lncRNA-locus1.bed"))
    mergedBed = bedMergeBlocks("test1", beds)
    assert mergedBed.toRow() == \
        ['chr1', '148682028', '148712560', 'test1', '0', '-', '148712560', '148712560', '0', '5', '151,335,582,854,304,', '0,1264,23019,26177,30228,']

def testFixScores(request):
    with open(ts.get_test_output_file(request, ".bed"), 'w') as fh:
        for bed in BedReader(ts.get_test_input_file(request, "fixscores.bed"), numStdCols=5, fixScores=True):
            bed.write(fh)
    ts.diff_results_expected(request, ".bed")
