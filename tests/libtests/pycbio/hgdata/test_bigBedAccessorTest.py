# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.bigBedAccessor import BigBedAccessor
from pycbio.hgdata.bed import BedReader

# note: test bigBed are check in as a binary to avoid need to have tools
# and chrom files to convert on the file.  Recreate with:
#
#  bedToBigBed -tab -type=bed12+4 input/bed12extra.bed /hive/data/genomes/hg38/chrom.sizes input/bed12extra.bigBed
#

def _loadBed12Extra(request):
    return tuple(BedReader(ts.get_test_input_file(request, "bed12extra.bed"), numStdCols=4))

def _assertBeds(beds, bigBeds):
    assert len(beds) == len(bigBeds)
    for i in range(len(beds)):
        assert str(beds[i]) == str(bigBeds[i])

def testBed12Iter(request):
    with BigBedAccessor(ts.get_test_input_file(request, "bed12extra.bigBed"), numStdCols=12) as fh:
        fromBigBed = [b for b in fh]
    _assertBeds(_loadBed12Extra(request), fromBigBed)

def testBed12Rand(request):
    bed12extra = _loadBed12Extra(request)
    with BigBedAccessor(ts.get_test_input_file(request, "bed12extra.bigBed"), numStdCols=12) as fh:
        fromBigBed = []
        for bed in bed12extra:
            fromBigBed.extend(bb for bb in fh.overlapping(bed.chrom, bed.start, bed.end))
    _assertBeds(bed12extra, fromBigBed)

def testBed12NonOver(request):
    with BigBedAccessor(ts.get_test_input_file(request, "bed12extra.bigBed"), numStdCols=12) as fh:
        fromBigBed = list(fh.overlapping("chr1", 60000, 61000))
    _assertBeds([], fromBigBed)

def testBed12NonChrom(request):
    with BigBedAccessor(ts.get_test_input_file(request, "bed12extra.bigBed"), numStdCols=12) as fh:
        fromBigBed = list(fh.overlapping("chrNotThere", 35244, 36073))
    _assertBeds([], fromBigBed)
