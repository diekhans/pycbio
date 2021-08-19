# Copyright 2006-2014 Mark Diekhans
import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

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
        # overlap with None strand (overlaps either strand)
        c4 = Coords("chr22", 50000000, 60000000, strand=None, size=50818468)
        self.assertTrue(c3.overlaps(c4))
        self.assertTrue(c4.overlaps(c3))
        self.assertTrue(c1.overlaps(c4))
        self.assertTrue(c4.overlaps(c1))

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

    def FIXME_testCoordsCmpNoStrand(self):
        # strand None comparison must be handled carefully, can't do None < None
        cs = [Coords("chr22", 10200, 20000),
              Coords("chr1", 90200, 990000),
              Coords("chr22", 10000, 20000),
              Coords("chr22", 10000, 10000)]

        self.assertEqual(sorted(cs, key=lambda c: (c.name, c.start, c.end)),
                         sorted(cs))

    def FIXME_testCoordsCmpStrand(self):
        cs = [Coords("chr22", 10200, 20000, '-'),
              Coords("chr1", 90200, 990000, '+'),
              Coords("chr22", 10400, 20000, '-'),
              Coords("chr22", 10200, 20000, '+'),
              Coords("chr22", 10000, 10000, '-')]
        self.assertEqual(sorted(cs, key=lambda c: (c.name, c.start, c.end, c.strand)),
                         sorted(cs))

    def FIXME_testCoordsSortRegress(self):
        # regression from real data
        cs = [Coords(name='chrY', start=57183100, end=57197337),
              Coords(name='chrY', start=22439592, end=22442458),
              Coords(name='chrY', start=22143965, end=22146831),
              Coords(name='chrY', start=9753155, end=9775289),
              Coords(name='chrY', start=6389430, end=6411564),
              Coords(name='chrX', start=155996580, end=156010817),
              Coords(name='chrX', start=65269912, end=65273019),
              Coords(name='chr22', start=29436533, end=29479868),
              Coords(name='chr19', start=54531691, end=54545771),
              Coords(name='chr17', start=15674475, end=15675643),
              Coords(name='chr16', start=90004870, end=90020890),
              Coords(name='chr14', start=61569404, end=61658696),
              Coords(name='chr12', start=68472740, end=68474902),
              Coords(name='chr12', start=30978307, end=31007010),
              Coords(name='chr12', start=8940360, end=8950761),
              Coords(name='chr12', start=2793969, end=2805423),
              Coords(name='chr11', start=64304496, end=64316743),
              Coords(name='chr11', start=61746492, end=61758655),
              Coords(name='chr10', start=119620067, end=119621880),
              Coords(name='chr7', start=127587385, end=127591700),
              Coords(name='chr7', start=100569130, end=100571136),
              Coords(name='chr7', start=26533120, end=26539788),
              Coords(name='chr6', start=143494811, end=143512720),
              Coords(name='chr4', start=139698143, end=139699554),
              Coords(name='chr4', start=11393149, end=11430564),
              Coords(name='chr3', start=50154044, end=50189075),
              Coords(name='chr2', start=237048598, end=237057167),
              Coords(name='chr2', start=72129237, end=72148862),
              Coords(name='chr2', start=37230630, end=37253403),
              Coords(name='chr1', start=171136739, end=171161568),
              Coords(name='chr1', start=67521298, end=67532612),
              Coords(name='chr1', start=1698941, end=1701782),
              Coords(name='chr1', start=922922, end=944575),
              Coords(name='chr5', start=270669, end=438291)
        ]
        self.assertEqual(sorted(cs, key=lambda c: (c.name, c.start, c.end, c.strand)),
                         sorted(cs))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CoordsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
