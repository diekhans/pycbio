# Copyright 2006-2025 Mark Diekhans
import os
import os.path as osp
import sys
import pickle
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.sys import fileOps
from pycbio.hgdata.bed import Bed, BedBlock, BedTable, BedReader, bedFromPsl, bedMergeBlocks, BedException, encodeRow, defaultIfNone
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

def testBedMergeOverlapping(request):
    """Test merging BEDs with overlapping blocks"""
    bed1 = Bed("chr1", 100, 300, "bed1", strand="+", blocks=[BedBlock(100, 150), BedBlock(200, 300)])
    bed2 = Bed("chr1", 120, 350, "bed2", strand="+", blocks=[BedBlock(120, 180), BedBlock(250, 350)])
    mergedBed = bedMergeBlocks("merged", [bed1, bed2])
    assert mergedBed.chrom == "chr1"
    assert mergedBed.chromStart == 100
    assert mergedBed.chromEnd == 350
    assert mergedBed.name == "merged"
    assert mergedBed.strand == "+"
    # Should merge into: [100-180, 200-350]
    assert len(mergedBed.blocks) == 2
    assert mergedBed.blocks[0] == BedBlock(100, 180)
    assert mergedBed.blocks[1] == BedBlock(200, 350)

def testBedMergeAdjacent(request):
    """Test merging BEDs with adjacent blocks that should be joined"""
    bed1 = Bed("chr2", 100, 250, "bed1", strand="-", blocks=[BedBlock(100, 150)])
    bed2 = Bed("chr2", 150, 250, "bed2", strand="-", blocks=[BedBlock(150, 250)])
    mergedBed = bedMergeBlocks("merged", [bed1, bed2])
    # Adjacent blocks should merge into one
    assert len(mergedBed.blocks) == 1
    assert mergedBed.blocks[0] == BedBlock(100, 250)

def testBedMergeNonOverlapping(request):
    """Test merging BEDs with non-overlapping blocks"""
    bed1 = Bed("chr3", 100, 150, "bed1", strand="+", blocks=[BedBlock(100, 150)])
    bed2 = Bed("chr3", 300, 350, "bed2", strand="+", blocks=[BedBlock(300, 350)])
    mergedBed = bedMergeBlocks("merged", [bed1, bed2])
    assert mergedBed.chromStart == 100
    assert mergedBed.chromEnd == 350
    # Non-overlapping blocks should remain separate
    assert len(mergedBed.blocks) == 2
    assert mergedBed.blocks[0] == BedBlock(100, 150)
    assert mergedBed.blocks[1] == BedBlock(300, 350)

def testBedMergeThickBounds(request):
    """Test that thickStart/thickEnd are properly merged"""
    bed1 = Bed("chr4", 100, 300, "bed1", strand="+", thickStart=120, thickEnd=200,
               blocks=[BedBlock(100, 300)])
    bed2 = Bed("chr4", 150, 400, "bed2", strand="+", thickStart=180, thickEnd=350,
               blocks=[BedBlock(150, 400)])
    mergedBed = bedMergeBlocks("merged", [bed1, bed2])
    # Should take min of thickStart and max of thickEnd
    assert mergedBed.thickStart == 120
    assert mergedBed.thickEnd == 350

def testBedMergeSingle(request):
    """Test merging a single BED (should return a copy)"""
    bed1 = Bed("chr5", 100, 300, "bed1", strand="+", blocks=[BedBlock(100, 150), BedBlock(200, 300)])
    mergedBed = bedMergeBlocks("merged", [bed1])
    assert mergedBed.chrom == "chr5"
    assert mergedBed.chromStart == 100
    assert mergedBed.chromEnd == 300
    assert mergedBed.name == "merged"
    assert len(mergedBed.blocks) == 2

def testBedMergeMultipleComplex(request):
    """Test merging multiple BEDs with complex overlapping patterns"""
    bed1 = Bed("chr6", 100, 400, "bed1", strand="+",
               blocks=[BedBlock(100, 150), BedBlock(200, 250), BedBlock(350, 400)])
    bed2 = Bed("chr6", 120, 380, "bed2", strand="+",
               blocks=[BedBlock(120, 180), BedBlock(240, 280), BedBlock(360, 380)])
    bed3 = Bed("chr6", 130, 420, "bed3", strand="+",
               blocks=[BedBlock(130, 160), BedBlock(275, 285), BedBlock(400, 420)])
    mergedBed = bedMergeBlocks("merged", [bed1, bed2, bed3])
    # Should merge overlapping/adjacent blocks
    assert mergedBed.chromStart == 100
    assert mergedBed.chromEnd == 420
    assert len(mergedBed.blocks) == 3
    assert mergedBed.blocks[0] == BedBlock(100, 180)
    assert mergedBed.blocks[1] == BedBlock(200, 285)
    assert mergedBed.blocks[2] == BedBlock(350, 420)

def testBedMergeEmpty(request):
    """Test that merging empty list raises exception"""
    try:
        bedMergeBlocks("merged", [])
        assert False, "Expected BedException"
    except BedException as e:
        assert "can't merge list with no BEDs" in str(e)

def testBedMergeDifferentChroms(request):
    """Test that merging BEDs on different chromosomes raises exception"""
    bed1 = Bed("chr1", 100, 200, "bed1", strand="+", blocks=[BedBlock(100, 200)])
    bed2 = Bed("chr2", 100, 200, "bed2", strand="+", blocks=[BedBlock(100, 200)])
    try:
        bedMergeBlocks("merged", [bed1, bed2])
        assert False, "Expected BedException"
    except BedException as e:
        assert "different chromosomes" in str(e)

def testBedMergeDifferentStrands(request):
    """Test that merging BEDs on different strands raises exception"""
    bed1 = Bed("chr1", 100, 200, "bed1", strand="+", blocks=[BedBlock(100, 200)])
    bed2 = Bed("chr1", 100, 200, "bed2", strand="-", blocks=[BedBlock(100, 200)])
    try:
        bedMergeBlocks("merged", [bed1, bed2])
        assert False, "Expected BedException"
    except BedException as e:
        assert "different strands" in str(e)

def testBedMergeUnstranded(request):
    """Test merging BEDs on different strands with stranded=False"""
    bed1 = Bed("chr1", 100, 200, "bed1", strand="+", blocks=[BedBlock(100, 200)])
    bed2 = Bed("chr1", 150, 300, "bed2", strand="-", blocks=[BedBlock(150, 300)])
    mergedBed = bedMergeBlocks("merged", [bed1, bed2], stranded=False)
    assert mergedBed.strand == "+"
    assert mergedBed.chromStart == 100
    assert mergedBed.chromEnd == 300
    assert len(mergedBed.blocks) == 1
    assert mergedBed.blocks[0] == BedBlock(100, 300)

def testBedMergeDifferentNumStdCols(request):
    """Test that merging BEDs with different numStdCols raises exception"""
    bed1 = Bed("chr1", 100, 200, "bed1", strand="+", blocks=[BedBlock(100, 200)])
    bed2 = Bed("chr1", 100, 200, "bed2", strand="+", numStdCols=6)
    try:
        bedMergeBlocks("merged", [bed1, bed2])
        assert False, "Expected BedException"
    except BedException as e:
        assert "standard columns" in str(e)

def testFixScores(request):
    with open(ts.get_test_output_file(request, ".bed"), 'w') as fh:
        for bed in BedReader(ts.get_test_input_file(request, "fixscores.bed"), numStdCols=5, fixScores=True):
            bed.write(fh)
    ts.diff_results_expected(request, ".bed")

def testAddExtra(request):
    testRow = ["chrZ", "1000", "2000", "fred"]
    extraCols = ["barney", "wilma"]
    bed = Bed.parse(testRow)
    assert bed.numStdCols == 4
    assert bed.numColumns == 4
    bed.addExtraCols(extraCols)
    assert bed.numStdCols == 4
    assert bed.numColumns == 6
    assert bed.toRow() == testRow + extraCols
    assert isinstance(bed.extraCols, tuple)

###
# BedBlock tests
###
def testBedBlockLen(request):
    """Test BedBlock.__len__"""
    blk = BedBlock(100, 250)
    assert len(blk) == 150

def testBedBlockStr(request):
    """Test BedBlock.__str__"""
    blk = BedBlock(100, 250)
    assert str(blk) == "100-250"

###
# Bed property tests
###
def testBedStartEndAliases(request):
    """Test start/end property aliases"""
    bed = Bed("chr1", 100, 500, "test")
    assert bed.start == 100
    assert bed.end == 500
    assert bed.start == bed.chromStart
    assert bed.end == bed.chromEnd

def testBedBlockCount(request):
    """Test blockCount property"""
    # With blocks
    bed = Bed("chr1", 100, 500, "test", strand="+",
              blocks=[BedBlock(100, 200), BedBlock(300, 500)])
    assert bed.blockCount == 2

    # Without blocks
    bed = Bed("chr1", 100, 500, "test")
    assert bed.blockCount == 0

def testBedSpan(request):
    """Test span property"""
    bed = Bed("chr1", 100, 500, "test")
    assert bed.span == 400

def testBedCoverage(request):
    """Test coverage property"""
    # With blocks - coverage is sum of block lengths
    bed = Bed("chr1", 100, 500, "test", strand="+",
              blocks=[BedBlock(100, 200), BedBlock(300, 500)])
    assert bed.coverage == 300  # 100 + 200

    # Without blocks - coverage equals span
    bed = Bed("chr1", 100, 500, "test")
    assert bed.coverage == 400

###
# Bed.parse tests for various column counts
###
def testParseBed3(request):
    """Test parsing BED3"""
    bed = Bed.parse(["chr1", "100", "200"])
    assert bed.chrom == "chr1"
    assert bed.chromStart == 100
    assert bed.chromEnd == 200
    assert bed.name is None
    assert bed.numStdCols == 3

def testParseBed4(request):
    """Test parsing BED4"""
    bed = Bed.parse(["chr1", "100", "200", "feat1"])
    assert bed.name == "feat1"
    assert bed.score is None
    assert bed.numStdCols == 4

def testParseBed6(request):
    """Test parsing BED6"""
    bed = Bed.parse(["chr1", "100", "200", "feat1", "500", "-"])
    assert bed.name == "feat1"
    assert bed.score == 500
    assert bed.strand == "-"
    assert bed.numStdCols == 6

def testParseBed8(request):
    """Test parsing BED8"""
    bed = Bed.parse(["chr1", "100", "200", "feat1", "500", "-", "120", "180"])
    assert bed.thickStart == 120
    assert bed.thickEnd == 180
    assert bed.numStdCols == 8

def testParseBed9(request):
    """Test parsing BED9"""
    bed = Bed.parse(["chr1", "100", "200", "feat1", "500", "-", "120", "180", "255,0,0"])
    assert bed.itemRgb == "255,0,0"
    assert bed.numStdCols == 9

###
# Helper function tests
###
def testDefaultIfNone(request):
    """Test defaultIfNone function"""
    assert defaultIfNone("value") == "value"
    assert defaultIfNone(None) == ""
    assert defaultIfNone(None, "default") == "default"
    assert defaultIfNone(123) == "123"
    assert defaultIfNone(None, 0) == "0"

def testEncodeRow(request):
    """Test encodeRow function"""
    row = ["a", 1, None, 2.5]
    encoded = encodeRow(row)
    assert encoded == ["a", "1", "", "2.5"]

###
# BedReader tests
###
def testBedReaderEmpty(request):
    """Test BedReader with empty file"""
    tmpfile = fileOps.tmpFileGet(suffix=".bed")
    beds = list(BedReader(tmpfile))
    assert len(beds) == 0
    os.unlink(tmpfile)
