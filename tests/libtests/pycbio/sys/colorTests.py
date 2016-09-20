# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.color import Color
from pycbio.sys.testCaseBase import TestCaseBase


class ColorTests(TestCaseBase):
    def assertRgb(self, color, r, g, b):
        self.assertAlmostEquals(color.red, r)
        self.assertAlmostEquals(color.green, g)
        self.assertAlmostEquals(color.blue, b)

    def assertHsv(self, color, h, s, v):
        self.assertAlmostEquals(color.hue, h)
        self.assertAlmostEquals(color.saturation, s)
        self.assertAlmostEquals(color.value, v)

    def testRealRgb(self):
        c = Color.fromRgb(0.5, 0.3, 0.4)
        self.assertRgb(c, 0.5, 0.3, 0.4)
        self.assertRgb(c.setRed(0), 0.0, 0.3, 0.4)
        self.assertRgb(c.setGreen(1.0), 0.5, 1.0, 0.4)
        self.assertRgb(c.setBlue(0.2), 0.5, 0.3, 0.2)
        rgb = c.rgb
        self.assertAlmostEquals(rgb[0], 0.5)
        self.assertAlmostEquals(rgb[1], 0.3)
        self.assertAlmostEquals(rgb[2], 0.4)
        self.assertEquals(c.rgb8, (128, 77, 102))
        self.assertHsv(c, 0.9166666666, 0.4, 0.5)
        self.assertHsv(c.setHue(0.2), 0.2, 0.4, 0.5)
        self.assertHsv(c.setSaturation(0.2), 0.9166666666, 0.2, 0.5)
        self.assertHsv(c.setValue(1.0), 0.9166666666, 0.4, 1.0)
        hsv = c.hsv
        self.assertAlmostEquals(hsv[0], 0.9166666666)
        self.assertAlmostEquals(hsv[1], 0.4)
        self.assertAlmostEquals(hsv[2], 0.5)
        self.assertEquals(c.hsvi, (330, 40, 50))
        self.assertEquals(c.toHtmlColor(), "#804d66")

    def testRegress(self):
        c = Color.fromRgb8(16, 78, 139)
        self.assertEquals(c.red8, 16)
        self.assertEquals(c.green8, 78)
        self.assertEquals(c.blue8, 139)
        self.assertEquals(c.toRgb8Str(), "16,78,139")
        self.assertEquals(c.toHsviStr(), "210,88,55")
        self.assertEquals(c.toHtmlColor(), "#104e8b")

    def testImmutable(self):
        c = Color.fromRgb8(16, 78, 139)
        with self.assertRaises(AttributeError):
            c.red = 0


# FIXME: many more tests needed

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ColorTests))
    return ts

if __name__ == '__main__':
    unittest.main()
