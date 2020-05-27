# Copyright 2006-2020 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.bigBedAccessor import BigBedAccessor
from pycbio.hgdata.bed import BedReader

# note: test bigBed are check in as a binary to avoid need to have tools
# and chrom files to convert on the file.  Recreate with:
#
#  bedToBigBed -tab -type=bed12+4 input/bed12extra.bed /hive/data/genomes/hg38/chrom.sizes input/bed12extra.bigBed
#

class BigBedAccessorTests(TestCaseBase):
    def _loadBed12Extra(self):
        return tuple(BedReader(self.getInputFile("bed12extra.bed"), numStdCols=4))

    def _assertBeds(self, beds, bigBeds):
        self.assertEqual(len(beds), len(bigBeds))
        for i in range(len(beds)):
            self.assertEqual(str(beds[i]), str(bigBeds[i]))

    def testBed12Iter(self):
        with BigBedAccessor(self.getInputFile("bed12extra.bigBed"), numStdCols=12) as fh:
            fromBigBed = [b for b in fh]
        self._assertBeds(self._loadBed12Extra(), fromBigBed)

    def testBed12Rand(self):
        bed12extra = self._loadBed12Extra()
        with BigBedAccessor(self.getInputFile("bed12extra.bigBed"), numStdCols=12) as fh:
            fromBigBed = []
            for bed in bed12extra:
                fromBigBed.extend(bb for bb in fh.overlapping(bed.chrom, bed.start, bed.end))
        self._assertBeds(bed12extra, fromBigBed)

    def testBed12NonOver(self):
        with BigBedAccessor(self.getInputFile("bed12extra.bigBed"), numStdCols=12) as fh:
            fromBigBed = list(fh.overlapping("chr1", 60000, 61000))
        self._assertBeds([], fromBigBed)

    def testBed12NonChrom(self):
        with BigBedAccessor(self.getInputFile("bed12extra.bigBed"), numStdCols=12) as fh:
            fromBigBed = list(fh.overlapping("chrNotThere", 35244, 36073))
        self._assertBeds([], fromBigBed)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(BigBedAccessorTests))
    return ts


if __name__ == '__main__':
    unittest.main()
