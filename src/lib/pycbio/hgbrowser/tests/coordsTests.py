# Copyright 2006-2014 Mark Diekhans
import unittest, sys, re
if __name__ == '__main__':
    sys.path.append("../../..")

from pycbio.hgbrowser.coords import Coords
from pycbio.sys.testCaseBase import TestCaseBase

class CoordsTests(TestCaseBase):
    def testCoordsCombined(self):
        c = Coords("chr22:10000-20000")
        self.assertEqual(c.chrom, "chr22")
        self.assertEqual(c.start, 10000)
        self.assertEqual(c.end, 20000)

    def testCoordsThree(self):
        c = Coords("chr22", 10000, "20000")  # int and str numbers
        self.assertEqual(c.chrom, "chr22")
        self.assertEqual(c.start, 10000)
        self.assertEqual(c.end, 20000)

    def testCoordsThreeNone(self):
        c = Coords("chr22", None, None)
        self.assertEqual(c.chrom, "chr22")
        self.assertEqual(c.start, None)
        self.assertEqual(c.end, None)

    def testCoordsCombinedKwArgs(self):
        c = Coords("chr22:10000-20000", db="hg38", chromSize=50818468)
        self.assertEqual(c.chrom, "chr22")
        self.assertEqual(c.start, 10000)
        self.assertEqual(c.end, 20000)
        self.assertEqual(c.db, "hg38")
        self.assertEqual(c.chromSize, 50818468)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CoordsTests))
    return ts

if __name__ == '__main__':
    unittest.main()
