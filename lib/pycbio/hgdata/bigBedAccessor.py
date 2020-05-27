# Copyright 2006-2020 Mark Diekhans
import pyBigWig
from pycbio.hgdata.bed import Bed

class BigBedAccessor(object):
    """Access a bigBed file either randomly or sequentially. It can be
    used as a context manager."""
    def __init__(self, bigBedFile, numStdCols=None):
        self.bigBedFile = bigBedFile
        self.bigBedFh = pyBigWig.open(bigBedFile)
        self.numStdCols = numStdCols

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self.bigBedFh is not None:
            try:
                self.bigBedFh.close()
            finally:
                self.bigBedFh = None

    def chromNames(self):
        return list(sorted(self.bigBedFh.chroms().keys()))

    def getChromSize(self, chrom):
        "get size or none if chrom does not exist"
        return self.bigBedFh.chroms().get(chrom)

    def _recToBed(self, chrom, entry):
        row = [chrom, str(entry[0]), str(entry[1])] + entry[2].split('\t')
        return Bed.parse(row, self.numStdCols)

    def overlapping(self, chrom, start, end):
        if chrom in self.bigBedFh.chroms():
            entries = self.bigBedFh.entries(chrom, start, end)
            if entries is not None:
                for entry in entries:
                    yield self._recToBed(chrom, entry)

    def __iter__(self):
        "iterating is not memory efficient"
        def gen(self):
            for chrom in self.chromNames():
                chromSize = self.getChromSize(chrom)
                for entry in self.bigBedFh.entries(chrom, 0, chromSize):
                    yield self._recToBed(chrom, entry)
        return gen(self)
