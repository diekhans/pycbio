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


def calcFreq(amt, total):
    "calculates a frequency, etc or zero if total is zero"
    return 0.0 if total == 0.0 else (float(amt) / float(total))


def fmtFreq(freq, precision=2):
    "format a frequency as a string to the specified precision"
    return "%0.*f" % (precision, freq)


def calcFmtFreq(amt, total, precision=2):
    "calculate and format a frequency"
    return fmtFreq(calcFreq(amt, total), precision)
