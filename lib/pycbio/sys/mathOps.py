# Copyright 2006-2017 Mark Diekhans
"""
Math operations
"""
import math


def roundToOrderOfMagnitude(n):
    """round up to nearest order of magnitude.  Rounding up for positive or zero, and
    down for negative."""
    # from http://stackoverflow.com/questions/7906996/algorithm-to-round-to-the-next-order-of-magnitude-in-r
    if n == 0:
        return 1
    logn = math.log10(abs(n))
    decimalPlaces = math.ceil(logn) if (logn > 0) else math.floor(logn) + 1
    rounded = math.pow(10, decimalPlaces)
    return -rounded if n < 0 else rounded


def calcFreq(amt, total, oneForUndef=False):
    """calculates a frequency or rate. Return the total is zero
     return zero, or one if oneForUndef is True """
    if total == 0.0:
        return 1.0 if oneForUndef else 0.0
    else:
        return amt / total


def fmtFreq(freq, precision=2):
    "format a frequency as a string to the specified precision"
    return "%0.*f" % (precision, freq)


def calcFmtFreq(amt, total, precision=2, oneForUndef=False):
    "calculate and format a frequency"
    return fmtFreq(calcFreq(amt, total, oneForUndef), precision)
