# Copyright 2006-2026 Mark Diekhans
import io
from pycbio.stats.histogram import Histogram


def _getBinInfo(b):
    return (b.idx, b.binMin, b.binMin + b.binSize, b.binSize, b.cnt, b.freq)

def _getBinsInfo(bins):
    return [_getBinInfo(b) for b in bins]

def testNumBins():
    "bins computed from a bin count are centered on the data range"
    h = Histogram([-1.0, 1.0], numBins=2)
    bins = h.build()
    assert _getBinsInfo(bins) == [(0, -2.0, 0.0, 2.0, 1, 0.0),
                                  (1, 0.0, 2.0, 2.0, 1, 0.0)]

def testBinSize():
    "bins computed from a bin size start at the data minimum"
    h = Histogram([-1.0, 1.0], binSize=1)
    bins = h.build()
    assert _getBinsInfo(bins) == [(0, -1.0, 0.0, 1, 1, 0.0),
                                  (1, 0.0, 1.0, 1, 1, 0.0)]

def testIntData():
    "an int bin index, and every value binned; the max lands in the last bin"
    h = Histogram(data=[1, 2, 3, 4, 10])
    bins = h.build()
    assert [b.cnt for b in bins] == [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]
    assert sum(b.cnt for b in bins) == 5
    assert [b.freq for b in bins] == [0.2, 0.2, 0.2, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2]

def testFloatData():
    h = Histogram(data=[1.5, 2.5, 3.5])
    bins = h.build()
    assert sum(b.cnt for b in bins) == 3
    assert h.numBinsUse == 10

def testTupleData():
    h = Histogram(data=[(1, 2), (5, 3), (10, 1)], isTupleData=True)
    bins = h.build()
    assert sum(b.cnt for b in bins) == 6

def testTruncMinMax():
    "values outside an explicit range are dropped when truncated"
    h = Histogram(data=[0, 5, 10], binMin=3, binMax=7, numBins=2,
                  truncMin=True, truncMax=True)
    bins = h.build()
    assert sum(b.cnt for b in bins) == 1

def testDump():
    "the use line names each value it prints"
    h = Histogram(data=list(range(1, 11)))
    fh = io.StringIO()
    h.dump(fh)
    lines = fh.getvalue().splitlines()
    assert lines[0] == "  data: len: 10  min: 1 max: 10"
    assert lines[2] == "  use:  num: 10 size: 1.0 min: 1 max: 10 floor: 0.5 ceil: 10.5"
