# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys import mathOps
from pycbio.sys.testCaseBase import TestCaseBase


class RoundToOrderOfMagnitudeTests(TestCaseBase):
    def __assertRound(self, expect, value):
        self.assertEquals(expect, mathOps.roundToOrderOfMagnitude(value))

    def testMagnitudeFifty(self):
        self.__assertRound(100, 50)

    def testMagnitudeFive(self):
        self.__assertRound(10, 5)

    def testMagnitudeZeroPointFive(self):
        self.__assertRound(1, 0.5)

    def testMagnitudeZeroPointZeroFive(self):
        self.__assertRound(0.1, 0.05)

    def testMagnitudeZeroPointZeroZeroFive(self):
        self.__assertRound(0.01, 0.005)

    def testMagnitudeNegativeFifty(self):
        self.__assertRound(-100, -50)

    def testMagnitudeNegativeFive(self):
        self.__assertRound(-10, -5)

    def testMagnitudeNegativeZeroPointFive(self):
        self.__assertRound(-1, -0.5)

    def testMagnitudeNegativeZeroPointZeroFive(self):
        self.__assertRound(-0.1, -0.05)

    def testMagnitudeNegativeZeroPointZeroZeroFive(self):
        self.__assertRound(-0.01, -0.005)

    def testMagnitudeZero(self):
        self.__assertRound(1, 0)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(RoundToOrderOfMagnitudeTests))
    return ts

if __name__ == '__main__':
    unittest.main()
