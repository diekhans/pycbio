import unittest, sys, string, cPickle
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.Color import Color
from pycbio.sys.TestCaseBase import TestCaseBase


class ColorTests(TestCaseBase):
    def assertRgb(self, color, r, g, b):
        self.assertAlmostEquals(color.getRed(), r)
        self.assertAlmostEquals(color.getGreen(), g)
        self.assertAlmostEquals(color.getBlue(), b)

    def assertHsv(self, color, h, s, v):
        self.assertAlmostEquals(color.getHue(), h)
        self.assertAlmostEquals(color.getSaturation(), s)
        self.assertAlmostEquals(color.getValue(), v)

    def testRealRgb(self):
        c = Color.fromRgb(0.5, 0.3, 0.4)
        self.assertRgb(c, 0.5, 0.3, 0.4)
        self.assertRgb(c.setRed(0), 0.0, 0.3, 0.4)
        self.assertRgb(c.setGreen(1.0), 0.5, 1.0, 0.4)
        self.assertRgb(c.setBlue(0.2), 0.5, 0.3, 0.2)
        rgb = c.getRgb()
        self.assertAlmostEquals(rgb[0], 0.5)
        self.assertAlmostEquals(rgb[1], 0.3)
        self.assertAlmostEquals(rgb[2], 0.4)
        self.assertEquals(c.getRgb8(), (128, 77, 102))
        self.assertHsv(c, 0.9166666666, 0.4, 0.5)
        self.assertHsv(c.setHue(0.2), 0.2, 0.4, 0.5)
        self.assertHsv(c.setSaturation(0.2), 0.9166666666, 0.2, 0.5)
        self.assertHsv(c.setValue(1.0), 0.9166666666, 0.4, 1.0)
        hsv = c.getHsv()
        self.assertAlmostEquals(hsv[0], 0.9166666666)
        self.assertAlmostEquals(hsv[1], 0.4)
        self.assertAlmostEquals(hsv[2], 0.5)
        self.assertEquals(c.getHsv8(), (234, 102, 128))

# FIXME: many more tests needed

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ColorTests))
    return suite

if __name__ == '__main__':
    unittest.main()