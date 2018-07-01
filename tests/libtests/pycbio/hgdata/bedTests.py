# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.bed import BedTable


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


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(BedTests))
    return ts


if __name__ == '__main__':
    unittest.main()
