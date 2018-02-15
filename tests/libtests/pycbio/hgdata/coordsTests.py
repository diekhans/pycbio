# Copyright 2006-2014 Mark Diekhans
import unittest
import sys

if __name__ == '__main__':
    sys.path.append("../../../../lib")

from pycbio.hgdata.coords import Coords
from pycbio.sys.testCaseBase import TestCaseBase


class CoordsTests(TestCaseBase):
    def testCoordsParse(self):
        c = Coords.parse("chr22:10000-20000")
        self.assertEqual(c.name, "chr22")
        self.assertEqual(c.start, 10000)
        self.assertEqual(c.end, 20000)

    def testCoordsParseNameOnly(self):
        c = Coords.parse("chr22")
        self.assertEqual(c.name, "chr22")
        self.assertEqual(c.start, None)
        self.assertEqual(c.end, None)

    def testCoordsParseNameOnlySize(self):
        c = Coords.parse("chr22", size=50818468)
        self.assertEqual(c.name, "chr22")
        self.assertEqual(c.start, 0)
        self.assertEqual(c.end, 50818468)

    def testCoordsSimple(self):
        c = Coords("chr22", 10000, 20000)
        self.assertEqual(c.name, "chr22")
        self.assertEqual(c.start, 10000)
        self.assertEqual(c.end, 20000)

    def testCoordsNone(self):
        c = Coords("chr22", None, None)
        self.assertEqual(c.name, "chr22")
        self.assertEqual(c.start, None)
        self.assertEqual(c.end, None)

    def testCoordsParseExtra(self):
        c = Coords.parse("chr22:10000-20000", strand='-', size=50818468)
        self.assertEqual(c.name, "chr22")
        self.assertEqual(c.start, 10000)
        self.assertEqual(c.end, 20000)
        self.assertEqual(c.strand, '-')
        self.assertEqual(c.size, 50818468)

    def testCoordsReverse(self):
        c = Coords("chr22", 10000, 20000, strand='-', size=50818468)
        cr = Coords("chr22", 50798468, 50808468, strand='+', size=50818468)
        self.assertEqual(c.reverse(), cr)

    def testAbsReverse(self):
        c = Coords("chr22", 50798468, 50808468, strand='-', size=50818468)
        ca = Coords("chr22", 10000, 20000, strand='+', size=50818468)
        self.assertEqual(c.abs(), ca)

    def testIntersect(self):
        c1 = Coords("chr22", 50000000, 60000000, strand='-', size=50818468)
        c2 = Coords("chr22", 45000000, 55000000, strand='-', size=50818468)
        ci = c1.intersect(c2)
        self.assertEqual(ci, Coords("chr22", 50000000, 55000000, strand='-', size=50818468))



def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CoordsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
