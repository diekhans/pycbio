# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.stats.histogram import Histogram

# FIXME: not implemented


def _getBinInfo(self, b):
    return (b.idx, b.binMin, b.binMin + b.binSize, b.binSize, b.cnt, b.freq)

def _getBinsInfo(self, bins):
    return [self._getBinInfo(b) for b in bins]

def X_testNumBins(self):
    h = Histogram([-1.0, 1.0], numBins=2)
    bins = h.build()
    assert self._getBinsInfo(bins) == [(0, -2.0, 0.0, 2.0, 1, 0.0),
                                       (1, 0.0, 2.0, 2.0, 1, 0.0)]

def X_testBinSize(self):
    # FIXME: doesn't work
    h = Histogram([-1.0, 1.0], binSize=1)
    h.dump(sys.stdout)
    bins = h.build()
    assert self._getBinsInfo(bins) == [(0, -2.0, 0.0, 2.0, 1, 0.0),
                                       (1, 0.0, 2.0, 2.0, 1, 0.0)]
