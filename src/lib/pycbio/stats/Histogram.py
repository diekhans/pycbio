from pycbio.sys.fileOps import prLine, prRowv
from pycbio.sys.typeOps import isListLike

class Bin(object):
    "A bin in the histogram"
    def __init__(self, histo, idx, binMin, binSize):
        self.histo = histo
        self.idx = idx
        self.binMin = binMin
        self.binSize = binSize
        self.cnt = 0
        self.freq = 0.0

    def getCenter(self):
        "return center point of bin"
        return self.binMin+(self.binSize/2.0)

    def __str__(self):
        return "bin: "+ str(self.idx) + " min: " + str(self.binMin) + " size: " + str(self.binSize) + " cnt: " + str(self.cnt) + " freq: " + str(self.freq)
        
class NumData(list):
    "data consisting of individual numbers"
    def __init__(self):
        self.min = None
        self.max = None
        self.total = None

    def compute(self):
        "compute data range and total"
        self.min = min(self)
        self.max = max(self)
        self.total = sum(self)

class NumCntData(list):
    "data consisting of tuples of numbers and counts"
    def __init__(self):
        self.min = None
        self.max = None
        self.total = None

    def compute(self):
        "compute data range and total"
        self.min = self.max = self[0][0]
        self.total = 0
        for item in self:
            val = item[0]
            if val < self.min:
                self.min = val
            if val > self.max:
                self.max = val
            self.total += item[1]*val

class Histogram(object):
    """Bin data into a histogram for ploting or other purposes.
    Data items can either be single numbers (floats or ints), or
    tuples of (value, count).
    """

    def __init__(self, data=None, isTupleData=False):
        "create histogram, optionally adding data"
        # parameters controling histogram
        self.truncMin = False
        self.truncMax = False
        self.binMin = None
        self.binMax = None
        self.binSize = None
        self.numBins = None

        self.isTupleData = isTupleData
        if isTupleData:
            self.data = NumCntData()
        else:
            self.data = NumData()

        # these are computed automatically if the the value is not specified
        # above.  This allows changing the above values and rebinning
        self.binMinUse = None
        self.binMaxUse = None
        self.binSizeUse = None
        self.numBinsUse = None

        if (data != None):
            self.data.extend(data)

    def addItem(self, item):
        "add a single data item of the approriate type"
        self.data.append(item)

    def addData(self, data):
        "add a sequence of data items"
        self.data.extend(data)

    def addFile(self, fname, type=int, valCol=0):
        "add from a tab separated file of values of the specfied type"
        assert(not self.isTupleData)
        fh = open(fname)
        for line in fh:
            line=line[0:-1]
            row = line.split("\t")
            self.data.append(type(row[valCol]))
        fh.close()

    def addTupleFile(self, fname, type=int, valCol=0, cntCol=1):
        "add from a tab separated file of values of the specfied type and counts"
        assert(self.isTupleData)
        fh = open(fname)
        for line in fh:
            line=line[0:-1]
            row = line.split("\t")
            self.data.append((type(row[valCol]), int(row[cntCol])))
        fh.close()

    def _calcParams(self):
        "Calculate binning paramters"
        self.data.compute()
        self.binMinUse = self.binMin
        if self.binMinUse == None:
            self.binMinUse = self.data.min

        self.binMaxUse = self.binMax
        if self.binMaxUse == None:
            self.binMaxUse = self.data.max

        self.numBinsUse = self.numBins
        self.binSizeUse = self.binSize
        if (self.numBinsUse == None) and (self.binSizeUse == None):
            # default num bins and compute bin size from it below
            self.numBinsUse = 10
        if self.binSizeUse == None:
            # compute bin size from num bins
            self.binSizeUse = float(self.binMaxUse-self.binMinUse)/float(self.numBinsUse-1)
        else:
            # compute num bins from bin size
            self.numBinsUse = int((self.binMaxUse-self.binMinUse)/self.binSizeUse)+1

    def _getBin(self, val):
        "Get the integer bin number for a value"
        if self.binSizeUse == 0.0:
            return 0
        elif val < self.binMinUse:
            return 0
        elif val > self.binMaxUse:
            return self.numBinsUse - 1
        else:
            return int((val-self.binMinUse)/self.binSizeUse)

    def _inclItem(self, val):
        return (((not self.truncMin) or (item >= self.binMinUse))
                and ((not self.truncMax) or (item <= self.binMaxUse)))

    def build(self):
        "construct histogram from data, return list of bins"
        self._calcParams()
        histo = []
        for i in xrange(self.numBinsUse):
            histo.append(Bin(self, i, i*self.binSizeUse, self.binSizeUse))
        if self.isTupleData:
            for item in self.data:
                if self._inclItem(item[0]):
                    histo[self._getBin(item[0])].cnt += item[1]
        else:
            for item in self.data:
                if self._inclItem(item):
                    histo[self._getBin(item)].cnt += 1

        # compute frequences
        if self.data.total != 0.0:
            for bin in histo:
                bin.freq = bin.cnt / float(self.data.total)

        return histo

    def dump(self, fh, desc=None):
        if desc != None:
            prLine(fh, desc)
        self.build()
        prLine(fh, "  data:  len: ", len(self.data), "  min: ", self.data.min, "  max: ", self.data.max)
        prLine(fh, "  bins:  num: ", self.numBins, "  size: ", self.binSize, "  min: ", self.binMin, "  max: ", self.binMax)
        prLine(fh, "  use:  num: ", self.numBinsUse, "  size: ", self.binSizeUse, "  min: ", self.binMinUse, "  max: ", self.binMaxUse)
        
