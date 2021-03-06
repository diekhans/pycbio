# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.color import Color
from pycbio.sys.svgcolors import SvgColors
from pycbio.sys.testCaseBase import TestCaseBase


class ColorTests(TestCaseBase):
    def assertRgb(self, color, r, g, b):
        self.assertAlmostEqual(color.red, r)
        self.assertAlmostEqual(color.green, g)
        self.assertAlmostEqual(color.blue, b)

    def assertHsv(self, color, h, s, v):
        self.assertAlmostEqual(color.hue, h)
        self.assertAlmostEqual(color.saturation, s)
        self.assertAlmostEqual(color.value, v)

    def testRealRgb(self):
        c = Color.fromRgb(0.5, 0.3, 0.4)
        self.assertRgb(c, 0.5, 0.3, 0.4)
        self.assertRgb(c.setRed(0), 0.0, 0.3, 0.4)
        self.assertRgb(c.setGreen(1.0), 0.5, 1.0, 0.4)
        self.assertRgb(c.setBlue(0.2), 0.5, 0.3, 0.2)
        rgb = c.rgb
        self.assertAlmostEqual(rgb[0], 0.5)
        self.assertAlmostEqual(rgb[1], 0.3)
        self.assertAlmostEqual(rgb[2], 0.4)
        self.assertEqual(c.rgb8, (128, 76, 102))
        self.assertHsv(c, 0.9166666666, 0.4, 0.5)
        self.assertHsv(c.setHue(0.2), 0.2, 0.4, 0.5)
        self.assertHsv(c.setSaturation(0.2), 0.9166666666, 0.2, 0.5)
        self.assertHsv(c.setValue(1.0), 0.9166666666, 0.4, 1.0)
        hsv = c.hsv
        self.assertAlmostEqual(hsv[0], 0.9166666666)
        self.assertAlmostEqual(hsv[1], 0.4)
        self.assertAlmostEqual(hsv[2], 0.5)
        self.assertEqual(c.hsvi, (330, 40, 50))
        self.assertEqual(c.toHtmlColor(), "#804c66")

    def testHtmlColor(self):
        c = Color.fromHtmlColor("#804c66")
        self.assertEqual(c.toHtmlColor(), "#804c66")

    def testPackRgb8(self):
        self.assertEqual(Color.fromPackRgb8(0x008000), Color.fromRgb8(0x00, 0x80, 0x00))
        self.assertEqual(Color.fromPackRgb8(0xFFA510), Color.fromRgb8(0xFF, 0xA5, 0x10))
        self.assertEqual(Color.fromPackRgb8(0x008000).packRgb8, 0x008000)
        self.assertEqual(Color.fromPackRgb8(0xFFA510).packRgb8, 0xFFA510)

    def testRegress(self):
        c = Color.fromRgb8(16, 78, 139)
        self.assertEqual(c.red8, 16)
        self.assertEqual(c.green8, 78)
        self.assertEqual(c.blue8, 139)
        self.assertEqual(c.toRgb8Str(), "16,78,139")
        self.assertEqual(c.toHsviStr(), "210,88,55")
        self.assertEqual(c.toHtmlColor(), "#104e8b")

    def testImmutable(self):
        c = Color.fromRgb8(16, 78, 139)
        with self.assertRaises(AttributeError):
            c.red = 0


class SvgColorsTests(TestCaseBase):
    def testAliceBlue(self):
        self.assertEqual(SvgColors.aliceblue, Color.fromRgb8(0xf0, 0xf8, 0xff))

    def testBlack(self):
        self.assertEqual(SvgColors.black, Color.fromRgb(0.0, 0.0, 0.0))

    def testLookup(self):
        self.assertEqual(SvgColors.yellowgreen, SvgColors.lookup("yellowgreen"))

    def testLookupBad(self):
        with self.assertRaises(AttributeError):
            SvgColors.lookup("evil")

# FIXME: many more tests needed

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ColorTests))
    ts.addTest(unittest.makeSuite(SvgColorsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
