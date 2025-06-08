# Copyright 2006-2025 Mark Diekhans
import sys
import math
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys import mathOps


def _assertRound(expect, value):
    "asserted that value is same as expect when rounded to it's order of magnitude"
    assert mathOps.roundToOrderOfMagnitude(value) == expect

def testMagnitudeFifty():
    _assertRound(100, 50)

def testMagnitudeFive():
    _assertRound(10, 5)

def testMagnitudeZeroPointFive():
    _assertRound(1, 0.5)

def testMagnitudeZeroPointZeroFive():
    _assertRound(0.1, 0.05)

def testMagnitudeZeroPointZeroZeroFive():
    _assertRound(0.01, 0.005)

def testMagnitudeNegativeFifty():
    _assertRound(-100, -50)

def testMagnitudeNegativeFive():
    _assertRound(-10, -5)

def testMagnitudeNegativeZeroPointFive():
    _assertRound(-1, -0.5)

def testMagnitudeNegativeZeroPointZeroFive():
    _assertRound(-0.1, -0.05)

def testMagnitudeNegativeZeroPointZeroZeroFive():
    _assertRound(-0.01, -0.005)

def testMagnitudeZero():
    _assertRound(1, 0)

def testSafeDivInt0():
    assert math.isnan(mathOps.safeDiv(10, 0))

def testSafeDivFloat0():
    assert math.isnan(mathOps.safeDiv(10.1, 0.0))

def testSafeDivFloatNan():
    assert math.isnan(mathOps.safeDiv(10.1, math.nan))
