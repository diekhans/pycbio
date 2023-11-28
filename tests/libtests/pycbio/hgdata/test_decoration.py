# Copyright 2006-2023 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.decoration import Decoration, Glyph, BedBlock
from pycbio.sys.color import Color

def _mkBlock(start, size, off):
    return BedBlock(start + off, start + off + size)


class DecorationTests(TestCaseBase):

    def testDecoBlock(self):
        start = 11674801
        end = 11675720
        blocks = [_mkBlock(start, 15, 0),
                  _mkBlock(start, 93, 280),
                  _mkBlock(start, 63, 856)]
        deco = Decoration("chr1", start, end, "HORMA", "ENST00000697272.1", 11658917, 11675722,
                          strand='-', itemRgb=Color.fromRgb8(255, 0, 0), blocks=blocks,
                          fillColor=Color.fromRgb8(34, 139, 34, 128),
                          decoExtraCols=("Fred", "Wilma"))
        self.assertEqual(deco.toRow(),
                         ['chr1', '11674801', '11675720', 'HORMA', '0', '-', '11674801', '11675720', '255,0,0',
                          '3', '15,93,63,', '0,280,856,',
                          'chr1:11658917-11675722:ENST00000697272.1', 'block', '34,139,34,128', 'NA',
                          'Fred', 'Wilma'])

    def testDecoGlyoh(self):
        deco = Decoration("chr1", 11675147, 11675147, "del 105",
                          "ENST00000697274.1", 11675146, 11691811,
                          strand='-', itemRgb="255,0,0",
                          glyph=Glyph.Triangle,
                          decoExtraCols=("Barney", "Betty"))
        self.assertEqual(deco.toRow(),
                         ['chr1', '11675147', '11675147', 'del 105', '0', '-', '11675147', '11675147', '255,0,0',
                          '1', '0,', '0,', 'chr1:11675146-11691811:ENST00000697274.1', 'glyph', '255,0,0', 'Triangle',
                          'Barney', 'Betty'])

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(DecorationTests))
    return ts


if __name__ == '__main__':
    unittest.main()
