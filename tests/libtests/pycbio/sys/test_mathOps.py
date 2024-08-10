# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
import math
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys import mathOps
from pycbio.sys.testCaseBase import TestCaseBase


class RoundToOrderOfMagnitudeTests(TestCaseBase):
    def _assertRound(self, expect, value):
        "asserted that value is same as expect when rounded to it's order of magnitude"
        # FIXME: could this be done another way?
        self.assertEqual(expect, mathOps.roundToOrderOfMagnitude(value))

    def testMagnitudeFifty(self):
        self._assertRound(100, 50)

    def testMagnitudeFive(self):
        self._assertRound(10, 5)

    def testMagnitudeZeroPointFive(self):
        self._assertRound(1, 0.5)

    def testMagnitudeZeroPointZeroFive(self):
        self._assertRound(0.1, 0.05)

    def testMagnitudeZeroPointZeroZeroFive(self):
        self._assertRound(0.01, 0.005)

    def testMagnitudeNegativeFifty(self):
        self._assertRound(-100, -50)

    def testMagnitudeNegativeFive(self):
        self._assertRound(-10, -5)

    def testMagnitudeNegativeZeroPointFive(self):
        self._assertRound(-1, -0.5)

    def testMagnitudeNegativeZeroPointZeroFive(self):
        self._assertRound(-0.1, -0.05)

    def testMagnitudeNegativeZeroPointZeroZeroFive(self):
        self._assertRound(-0.01, -0.005)

    def testMagnitudeZero(self):
        self._assertRound(1, 0)

class TestMathOps(TestCaseBase):
    def testSafeDiv0(self):
        self.assertTrue(math.isnan(mathOps.safeDiv(10, 0)))

    def testSafeDivNan(self):
        self.assertTrue(math.isnan(mathOps.safeDiv(10, math.nan)))

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(RoundToOrderOfMagnitudeTests))
    return ts


if __name__ == '__main__':
    unittest.main()
