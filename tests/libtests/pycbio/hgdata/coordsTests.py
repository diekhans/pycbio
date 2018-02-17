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

    def testReverse(self):
        c = Coords("chr22", 10000, 20000, strand='-', size=50818468)
        cr = Coords("chr22", 50798468, 50808468, strand='+', size=50818468)
        self.assertEqual(c.reverse(), cr)
        self.assertEqual(c, cr.reverse())

    def testAbs(self):
        c = Coords("chr22", 50798468, 50808468, strand='-', size=50818468)
        ca = Coords("chr22", 10000, 20000, strand='+', size=50818468)
        self.assertEqual(c.abs(), ca)
        self.assertNotEqual(c, ca.abs())

    def testAdjust(self):
        c = Coords("chr22", 50798468, 50808468, strand='-', size=50818468)
        ca = c.adjust(start=50798486, strand=None)
        self.assertEqual(ca, Coords("chr22", 50798486, 50808468, strand=None, size=50818468))

    def testOverlaps(self):
        # strand-specific
        c1 = Coords("chr22", 50000000, 60000000, strand='-', size=50818468)
        c2 = Coords("chr22", 45000000, 55000000, strand='-', size=50818468)
        self.assertTrue(c1.overlaps(c2))
        self.assertTrue(c2.overlaps(c1))
        self.assertTrue(c1.reverse().overlaps(c2.reverse()))
        self.assertTrue(c1.abs().overlaps(c1.abs()))
        # reversing, strand does not match
        self.assertFalse(c1.overlaps(c2.reverse()))
        self.assertFalse(c1.reverse().overlaps(c2))
        # overlap coords, different strand
        c3 = Coords("chr22", 45000000, 55000000, strand='+', size=50818468)
        self.assertFalse(c1.overlaps(c3))
        # overlap with default strand
        c4 = Coords("chr22", 50000000, 60000000, strand=None, size=50818468)
        self.assertTrue(c3.overlaps(c4))
        self.assertTrue(c4.overlaps(c3))
        self.assertFalse(c1.overlaps(c4))
        self.assertFalse(c4.overlaps(c1))

    def testIntersect(self):
        # strand-specific
        c1 = Coords("chr22", 50000000, 60000000, strand='-', size=50818468)
        c2 = Coords("chr22", 45000000, 55000000, strand='-', size=50818468)
        ci = c1.intersect(c2)
        self.assertEqual(ci, Coords("chr22", 50000000, 55000000, strand='-', size=50818468))
        c1p = c1.adjust(strand='+')
        c2p = c2.adjust(strand='+')
        cip = c1p.intersect(c2p)
        self.assertEqual(cip, Coords("chr22", 50000000, 55000000, strand='+', size=50818468))
        # defaulted strand
        c2d = c2.adjust(strand=None)
        cid = c1p.intersect(c2d)
        self.assertEqual(cid, Coords("chr22", 50000000, 55000000, strand='+', size=50818468))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CoordsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
