import string
from pycbio.tsv.TabFile import TabFile
from pycbio.sys import fileOps
from pycbio.hgdata.AutoSql import intArraySplit, intArrayJoin
from pycbio.sys.Enumeration import Enumeration

## FIXME: build on TSV code, allow indices, add GenePredReader

CdsStat = Enumeration("CdsStat", [
    ("none", "none"),             # No CDS (non-coding)
    ("unknown", "unk"),           # CDS is unknown (coding, but not known)
    ("incomplete", "incmpl"),     # CDS is not complete at this end
    ("complete", "cmpl")])        # CDS is complete at this end

class Range(object):
    "start and end coordinates"
    __slots__ = ("start", "end")
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return (other != None) and (self.start == other.start) and (self.end == other.end)

    def __ne__(self, other):
        return  (other == None) or (self.start != other.start) or (self.end != other.end)

    def __str__(self):
        return str(self.start) + ".." + str(self.end)

class ExonFeatures(object):
    "object the holds the features of a single exon"
    __slots__ = ("utr5", "cds", "utr3")
        
    def __init__(self):
        self.utr5 = None
        self.cds = None
        self.utr3 = None

    def __str__(self):
        return "utr5=" + str(self.utr5) + " cds=" + str(self.cds) + " utr3=" + str(self.utr3)

class Exon(object):
    "an exon in a genePred annotation"
    __slots__ = ("gene", "iExon", "start", "end", "frame")

    def __init__(self, gene, iExon, start, end, frame=None):
        self.gene = gene
        self.iExon = iExon
        self.start = start
        self.end = end
        self.frame = frame

    def __str__(self):
        s = str(self.start) + "-" + str(self.end)
        if self.frame != None:
            s += "/" + str(frame)
        return s

    def getCdsExonIdx(self):
        if (self.gene.cdsStartIExon != None) and (self.gene.cdsStartIExon <= self.iExon) and (self.iExon <= self.gene.cdsEndIExon):
            return self.iExon - self.gene.cdsStartIExon
        else:
            return None

    def getCds(self):
        "get the start, end (Range object) of cds in this exon, or None if no CDS"
        cdsSt = self.start
        if cdsSt < self.gene.cdsStart:
            cdsSt = self.gene.cdsStart
        cdsEnd = self.end
        if cdsEnd > self.gene.cdsEnd:
            cdsEnd = self.gene.cdsEnd
        if cdsSt >= cdsEnd:
            return None
        else:
            return Range(cdsSt, cdsEnd)

    def featureSplit(self):
        """split exon into a length-3 tuple in the form (utr5, cds, utr3)
        where each element is either None, or (start, end).  utr5 is 5' UTR
        in the exon, utr3, is 3'UTR, and cds is coding sequence of the exon."""
        feats = ExonFeatures()

        # UTR before CDS in exon
        start = self.start
        if (start < self.gene.cdsStart):
            end = min(self.end, self.gene.cdsStart)
            if (self.gene.strand == "+"):
                feats.utr5 = Range(start, end)
            else:
                feats.utr3 = Range(start, end)
            start = end

        # CDS in exon
        if (start < self.end) and (start < self.gene.cdsEnd):
            end = min(self.end, self.gene.cdsEnd)
            feats.cds = Range(start, end)
            start = end

        # UTR after CDS in exon
        if (start < self.end) and (start >= self.gene.cdsEnd):
            if (self.gene.strand == "+"):
                feats.utr3 = Range(start, self.end)
            else:
                feats.utr5 = Range(start, self.end)

        return feats

    def contains(self, pos):
        "does exon contain pos?"
        return (self.start <= pos) and (pos < self.end)

    def overlaps(self, start, end):
        "does exon overlap range?"
        return (self.start < end) and (self.end > start)

    def size(self):
        "size of the exon"
        return self.end-self.start

class GenePred(object):
    """Object wrapper for a genePred"""
    def _parse(self, row):
        self.name = row[0]
        self.chrom = row[1]
        self.strand = row[2]
        self.txStart = int(row[3])
        self.txEnd = int(row[4])
        self.cdsStart = int(row[5])
        self.cdsEnd = int(row[6])
        exonStarts = intArraySplit(row[8])
        exonEnds = intArraySplit(row[9])
        iCol = 10
        numCols = len(row)
        self.id = None
        if iCol < numCols:  # 10
            self.id = int(row[iCol])
            iCol = iCol+1
        self.name2 = None
        if iCol < numCols:  # 11
            self.name2 = row[iCol]
            iCol = iCol+1
        self.cdsStartStat = None
        self.cdsEndStat = None
        if iCol < numCols:  # 12,13
            self.cdsStartStat = CdsStat.lookup(row[iCol])
            self.cdsEndStat = CdsStat.lookup(row[iCol+1])
            iCol = iCol+2
        exonFrames = None
        self.hasExonFrames = False
        if iCol < numCols:  # 14
            exonFrames = intArraySplit(row[iCol])
            iCol = iCol+1
            self.hasExonFrames = True

        # build array of exon objects
        self.exons = []
        frame = None
        self.cdsStartIExon = None
        self.cdsEndIExon = None
        for i in xrange(len(exonStarts)):
            if exonFrames != None:
                frame = exonFrames[i]
            self.addExon(exonStarts[i], exonEnds[i], frame)

    def _empty(self):
        self.name = None
        self.chrom = None
        self.strand = None
        self.txStart = None
        self.txEnd = None
        self.cdsStart = None
        self.cdsEnd = None
        self.id = None
        self.name2 = None
        self.cdsStartStat = None
        self.cdsEndStat = None
        self.cdsStartStat = None
        self.cdsEndStat = None
        self.hasExonFrames = False
        self.exons = []
        self.cdsStartIExon = None
        self.cdsEndIExon = None

    def __init__(self, row=None):
        "If row is not None, parse a row, otherwise initialize to empty state"
        if row != None:
            self._parse(row)
        else:
            self._empty()

    def addExon(self, exonStart, exonEnd, frame=None):
        "add an exon; which must be done in assending order"
        i = len(self.exons)
        self.exons.append(Exon(self, i, exonStart, exonEnd, frame))
        if (self.cdsStart < self.cdsEnd) and (exonStart < self.cdsEnd) and (exonEnd > self.cdsStart):
            if self.cdsStartIExon == None:
                self.cdsStartIExon = i
            self.cdsEndIExon = i

    def inCds(self, pos):
        "test if a position is in the CDS"
        return (self.cdsStart <= pos) and (pos < self.cdsEnd)

    def overlapsCds(self, startOrRange, end=None):
        "test if a position is in the CDS. startOrRange is a Range or Exon if end is None"
        if end == None:
            return (startOrRange.start < self.cdsEnd) and (startOrRange.end > self.cdsStart)
        else:
            return (startOrRange < self.cdsEnd) and (end > self.cdsStart)

    def sameCds(self, gene2):
        "test if another gene has the same CDS as this gene"
        if id(self) == id(gene2):
            return True # same object
        if (gene2.chrom != self.chrom) or (gene2.strand != self.strand) or (gene2.cdsStart != self.cdsStart) or (gene2.cdsEnd != self.cdsEnd):
            return False
        nCds1 = self.getNumCdsExons()
        nCds2 = gene2.getNumCdsExons()
        if (nCds1 != nCds2):
            return False

        # check each exon
        iCds2 = 0
        for iCds1 in xrange(nCds1):
            exon1 = self.getCdsExon(iCds1)
            exon2 = gene2.getCdsExon(iCds2)
            if (exon1.getCds() != exon2.getCds()) or (exon1.frame != exon2.frame):
                return False
            iCds2 += 1
        return True

    def hasCds(self):
        return (self.cdsStartIExon != None)

    def getLenExons(self):
        "get the total length of all exons"
        l = 0
        for e in self.exons:
            l += e.end - e.start
        return l

    def getLenCds(self):
        "get the total length of CDS"
        l = 0
        for e in self.exons:
            cds = e.getCds()
            if cds != None:
                l += cds.end - cds.start
        return l

    def getNumCdsExons(self):
        "get the number of exons containing CDS"
        if self.cdsStartIExon == None:
            return 0
        else:
            return (self.cdsEndIExon - self.cdsStartIExon)+1
    
    def getCdsExon(self, iCdsExon):
        "get a exon containing CDS, by CDS exon index"
        return self.exons[self.cdsStartIExon + iCdsExon]

    def getRow(self):
        row = [self.name, self.chrom, self.strand, str(self.txStart), str(self.txEnd), str(self.cdsStart), str(self.cdsEnd)]
        row.append(str(len(self.exons)))
        starts = []
        ends = []
        for e in self.exons:
            starts.append(e.start)
            ends.append(e.end)
        row.append(intArrayJoin(starts))
        row.append(intArrayJoin(ends))

        hasExt = (self.id != None) or (self.name2 != None) or (self.cdsStartStat != None) or self.hasExonFrames

        if self.id != None:
            row.append(str(self.id))
        elif hasExt:
            row.append("0");
        if self.name2 != None:
            row.append(self.name2)
        elif hasExt:
            row.append("");
        if self.cdsStartStat != None:
            row.append(str(self.cdsStartStat))
            row.append(str(self.cdsEndStat))
        elif hasExt:
            row.append(str(CdsStat.unknown))
            row.append(str(CdsStat.unknown))
        if self.hasExonFrames or  hasExt:
            frames = []
            if self.hasExonFrames:
                for e in self.exons:
                    frames.append(e.frame)
            else:
                for e in self.exons:
                    frames.append(-1)
            row.append(intArrayJoin(frames))
        return row

    def getFeatures(self):
        """Get each exon, split into features; see Exon.featureSplit.
        List is returned in positive strand order"""
        feats = []
        for e in self.exons:
            feats.append(e.featureSplit())
        return feats

    def findContainingExon(self, pos):
        "find the exon contain pos, or None"
        for exon in self:
            if exon.contains(pos):
                return exon
        return None

    def __str__(self):
        return string.join(self.getRow(), "\t")

    def write(self, fh):
        fh.write(str(self))
        fh.write("\n")
        
class GenePredTbl(TabFile):
    """Table of GenePred objects loaded from a tab-file"""
    # FIXME: two index flags is a hack
    def __init__(self, fileName, buildIdx=False, buildUniqIdx=False, buildRangeIdx=False):
        TabFile.__init__(self, fileName, rowClass=GenePred)
        if buildIdx and buildUniqIdx:
            raise Exception("can't specify both buildIdx and buildUniqIdx")
        self.names = None
        self.rangeMap = None
        if buildUniqIdx:
            self.names = dict()
            for row in self:
                if row.name in self.names:
                    raise Exception("gene with this name already in index: " + row.name)
                self.names[row.name] = row
        if buildIdx:
            from pycbio.sys.MultiDict import MultiDict
            self.names = MultiDict()
            for row in self:
                self.names.add(row.name, row)
        if buildRangeIdx:
            from pycbio.hgdata.RangeFinder import RangeFinder
            self.rangeMap = RangeFinder()
            for gene in self:
                self.rangeMap.add(gene.chrom, gene.txStart, gene.txEnd, gene, gene.strand)

    def getGeneSet(self):
        "get a set of all of the genes in the table"
        return set(self)

# FIXME: hacked in, above should use this

class GenePredReader(object):
    """Read genePreds from a tab file"""
    def __init__(self, fileName):
        self.fh = fileOps.opengz(fileName)

    def __iter__(self):
        return self

    def next(self):
        "GPR next"
        while True:
            line = self.fh.readline()
            if (line == ""):
                self.fh.close();
                raise StopIteration
            if not ((len(line) == 1) or line.startswith('#')):
                line = line[0:-1]  # drop newline
                return GenePred(line.split("\t"))
