# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
import pickle
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio import PycbioException
from pycbio.sys.color import Color
from pycbio.sys.svgcolors import SvgColors
from pycbio.sys.testCaseBase import TestCaseBase


class ColorTests(TestCaseBase):
    def assertRgb(self, color, r, g, b, a=None):
        self.assertAlmostEqual(color.red, r)
        self.assertAlmostEqual(color.green, g)
        self.assertAlmostEqual(color.blue, b)
        self.assertAlmostEqual(color.alpha, a)

    def assertHsv(self, color, h, s, v, a=None):
        self.assertAlmostEqual(color.hue, h)
        self.assertAlmostEqual(color.saturation, s)
        self.assertAlmostEqual(color.value, v)
        self.assertAlmostEqual(color.alpha, a)

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
        self.assertEqual(c.hsv8, (330, 40, 50))
        self.assertEqual(c.toHtmlColor(), "#804c66")

    def testRealRgba(self):
        c = Color.fromRgb(0.5, 0.3, 0.4, 0.9)
        self.assertRgb(c, 0.5, 0.3, 0.4, 0.9)
        self.assertRgb(c.setRed(0), 0.0, 0.3, 0.4, 0.9)
        self.assertRgb(c.setGreen(1.0), 0.5, 1.0, 0.4, 0.9)
        self.assertRgb(c.setBlue(0.2), 0.5, 0.3, 0.2, 0.9)
        self.assertRgb(c.setAlpha(0.7), 0.5, 0.3, 0.4, 0.7)
        rgba = c.rgba
        self.assertAlmostEqual(rgba[0], 0.5)
        self.assertAlmostEqual(rgba[1], 0.3)
        self.assertAlmostEqual(rgba[2], 0.4)
        self.assertAlmostEqual(rgba[3], 0.9)
        self.assertEqual(c.rgba8, (128, 76, 102, 230))
        self.assertHsv(c, 0.9166666666, 0.4, 0.5, 0.9)
        self.assertHsv(c.setHue(0.2), 0.2, 0.4, 0.5, 0.9)
        self.assertHsv(c.setSaturation(0.2), 0.9166666666, 0.2, 0.5, 0.9)
        self.assertHsv(c.setValue(1.0), 0.9166666666, 0.4, 1.0, 0.9)
        hsva = c.hsva
        self.assertAlmostEqual(hsva[0], 0.9166666666)
        self.assertAlmostEqual(hsva[1], 0.4)
        self.assertAlmostEqual(hsva[2], 0.5)
        self.assertAlmostEqual(hsva[3], 0.9)
        self.assertEqual(c.hsva8, (330, 40, 50, 230))

    def testHtmlColor(self):
        c = Color.fromHtmlColor("#804c66")
        self.assertEqual(c.toHtmlColor(), "#804c66")

    def testRgb8Str(self):
        self.assertEqual(Color.fromRgb8Str("255,182,3"), Color.fromRgb8(255, 182, 3))
        with self.assertRaisesRegex(ValueError, "invalid RGB8 color string: 255,182"):
            Color.fromRgb8Str("255,182")
        with self.assertRaisesRegex(ValueError, "invalid RGB8 color string: 255,182"):
            Color.fromRgb8Str("255,182,399")

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
        self.assertEqual(c.toHsv8Str(), "210,88,55")
        self.assertEqual(c.toHtmlColor(), "#104e8b")

    def testImmutable(self):
        c = Color.fromRgb8(16, 78, 139)
        with self.assertRaises(AttributeError):
            c.red = 0

    def testDistance(self):
        c1 = Color.fromRgb(0.5, 0.3, 0.4)
        c2 = Color.fromRgb(0.9, 0.5, 0.1)
        self.assertEqual(c1.distance(c1), 0.0)
        self.assertAlmostEqual(c1.distance(c2), 0.5385164807)


class SvgColorsTests(TestCaseBase):
    def testAliceBlue(self):
        self.assertEqual(SvgColors.aliceblue, Color.fromRgb8(0xf0, 0xf8, 0xff))

    def testBlack(self):
        self.assertEqual(SvgColors.black, Color.fromRgb(0.0, 0.0, 0.0))

    def testLookup(self):
        self.assertEqual(SvgColors.yellowgreen, SvgColors.lookup("yellowgreen"))

    def testLoopErr(self):
        with self.assertRaisesRegex(PycbioException, "^unknown SVG color 'fred'$"):
            SvgColors.lookup("fred")

    def testLookupBad(self):
        with self.assertRaisesRegex(PycbioException, "^unknown SVG color 'evil'$"):
            SvgColors.lookup("evil")

    def testGetColors(self):
        self.assertTrue("whitesmoke" in SvgColors.getNames())
        self.assertTrue("skyblue" in SvgColors.getNames())

    def testClosest(self):
        self.assertEqual(SvgColors.getClosestName(SvgColors.skyblue), "skyblue")
        self.assertEqual(SvgColors.getClosestColor(SvgColors.skyblue), SvgColors.skyblue)

        # skyblue is 0x87ceeb
        near = Color.fromPackRgb8(0x87ceed)
        self.assertEqual(SvgColors.getClosestName(near), "skyblue")
        self.assertEqual(SvgColors.getClosestColor(near), SvgColors.skyblue)

    def testGetName(self):
        self.assertEqual(SvgColors.getName(SvgColors.skyblue), "skyblue")

    def testGetNameObjErr(self):
        with self.assertRaisesRegex(PycbioException, "^object is not a Color '<class 'dict'>'$"):
            SvgColors.getName(dict())

    def testGetNameNotSvgErr(self):
        with self.assertRaisesRegex(PycbioException, "^color is not an SVG color object '0.1200,0.4500,0.0010'$"):
            SvgColors.getName(Color.fromRgb(0.12, 0.45, 0.001))

    def testComplementary(self):
        c1 = Color.fromRgb(0.5, 0.3, 0.4)
        self.assertEqual(c1.complementary(), Color.fromRgb(0.5, 0.7, 0.6))

    def testPickle(self):
        c1 = Color.fromRgb(0.5, 0.3, 0.4)
        c1pkl = pickle.dumps(c1)
        c2 = pickle.loads(c1pkl)
        self.assertEqual(c1, c2)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ColorTests))
    ts.addTest(unittest.makeSuite(SvgColorsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
