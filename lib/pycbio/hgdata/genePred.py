# Copyright 2006-2012 Mark Diekhans
import copy
from collections import defaultdict
from pycbio.tsv.tabFile import TabFileReader
from pycbio.hgdata.autoSql import intArraySplit, intArrayJoin
from pycbio.sys.symEnum import SymEnum, SymEnumValue
from pycbio.sys import PycbioException


# FIXME range and exon overlap functions are inconsistent.  exon should inherit from range.
# FIXME needs many more tests


class CdsStat(SymEnum):
    none = SymEnumValue("none", "none")                # No CDS (non-coding)
    unknown = SymEnumValue("unknown", "unk")           # CDS is unknown (coding, but not known)
    incomplete = SymEnumValue("incomplete", "incmpl")  # CDS is not complete at this end
    complete = SymEnumValue("complete", "cmpl")        # CDS is complete at this end


genePredColumns = ("name", "chrom", "strand", "txStart", "txEnd", "cdsStart", "cdsEnd", "exonCount", "exonStarts", "exonEnds", "score", "name2", "cdsStartStat", "cdsEndStat", "exonFrames")
genePredExtColumns = ("name", "chrom", "strand", "txStart", "txEnd", "cdsStart", "cdsEnd", "exonCount", "exonStarts", "exonEnds")


class Range(object):
    "start and end coordinates"
    __slots__ = ("start", "end")
    # FIXME: maybe base class for coords?

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return (other is not None) and (self.start == other.start) and (self.end == other.end)

    def __ne__(self, other):
        return (other is None) or (self.start != other.start) or (self.end != other.end)

    def size(self):
        return self.end - self.start

    def __len__(self):
        return self.end - self.start

    def overlapAmt(self, other):
        maxStart = max(self.start, other.start)
        minEnd = min(self.end, other.end)
        return (minEnd - maxStart) if maxStart < minEnd else 0

    def overlaps(self, other):
        return (self.start < other.end) and (self.end > other.start)

    def __str__(self):
        return str(self.start) + ".." + str(self.end)

    def reverse(self, chromSize):
        "get a range on the opposite strand"
        return Range(chromSize - self.end, chromSize - self.start)


class ExonFeatures(object):
    "object the holds the features of a single exon"
    __slots__ = ("utr5", "cds", "utr3")

    def __init__(self, utr5=None, cds=None, utr3=None):
        self.utr5 = utr5
        self.cds = cds
        self.utr3 = utr3

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
        if self.frame is not None:
            s += "/" + str(self.frame)
        return s

    def getCdsExonIdx(self):
        if (self.gene.cdsStartIExon is not None) and (self.gene.cdsStartIExon <= self.iExon) and (self.iExon <= self.gene.cdsEndIExon):
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
`        where each element is either None, or (start, end).  utr5 is 5' UTR
        in the exon, utr3, is 3'UTR, and cds is coding sequence of the exon."""
        feats = ExonFeatures()

        # UTR before CDS in exon
        start = self.start
        if (start < self.gene.cdsStart):
            end = min(self.end, self.gene.cdsStart)
            if self.gene.inDirectionOfTranscription():
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
            if self.gene.inDirectionOfTranscription():
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

    def overlapAmt(self, start, end):
        maxStart = max(self.start, start)
        minEnd = min(self.end, end)
        return (minEnd - maxStart) if maxStart < minEnd else 0

    def size(self):
        "size of the exon"
        return self.end - self.start

    def getRelCoords(self, chromSize):
        "get a range object of strand-relative coordinates"
        if self.gene.inDirectionOfTranscription():
            return Range(self.start, self.end)
        else:
            return Range(chromSize - self.end, chromSize - self.start)


class GenePred(object):
    """Object wrapper for a genePred"""

    def _buildExons(self, exonStarts, exonEnds, exonFrames):
        "build array of exon objects"
        self.exons = []
        frame = None
        self.cdsStartIExon = None
        self.cdsEndIExon = None
        for i in range(len(exonStarts)):
            if exonFrames is not None:
                frame = exonFrames[i]
            self.addExon(exonStarts[i], exonEnds[i], frame)

    def _initParse(self, row):
        self.name = row[0]
        self.chrom = row[1]
        self.strand = row[2]
        self.strandRel = False    # are these strand-relative coordinates
        self.txStart = int(row[3])
        self.txEnd = int(row[4])
        self.cdsStart = int(row[5])
        self.cdsEnd = int(row[6])
        exonStarts = intArraySplit(row[8])
        exonEnds = intArraySplit(row[9])
        iCol = 10
        numCols = len(row)
        self.score = None
        if iCol < numCols:  # 10
            self.score = int(row[iCol])
            iCol = iCol + 1
        self.name2 = None
        if iCol < numCols:  # 11
            self.name2 = row[iCol]
            iCol = iCol + 1
        self.cdsStartStat = None
        self.cdsEndStat = None
        if iCol < numCols:  # 12,13
            self.cdsStartStat = CdsStat(row[iCol])
            self.cdsEndStat = CdsStat(row[iCol + 1])
            iCol = iCol + 2
        exonFrames = None
        self.hasExonFrames = False
        if iCol < numCols:  # 14
            exonFrames = intArraySplit(row[iCol])
            iCol = iCol + 1
            self.hasExonFrames = True
        self._buildExons(exonStarts, exonEnds, exonFrames)

    @staticmethod
    def _colOrNone(row, dbColIdxMap, colName, typeCnv):
        idx = dbColIdxMap.get(colName)
        return None if (idx is None) else typeCnv(row[idx])

    def _initDb(self, row, dbColIdxMap):
        self.name = row[dbColIdxMap["name"]]
        self.chrom = row[dbColIdxMap["chrom"]]
        self.strand = row[dbColIdxMap["strand"]]
        self.strandRel = False    # are these strand-relative coordinates
        self.txStart = int(row[dbColIdxMap["txStart"]])
        self.txEnd = int(row[dbColIdxMap["txEnd"]])
        self.cdsStart = int(row[dbColIdxMap["cdsStart"]])
        self.cdsEnd = int(row[dbColIdxMap["cdsEnd"]])
        exonStarts = intArraySplit(row[dbColIdxMap["exonStarts"]])
        exonEnds = intArraySplit(row[dbColIdxMap["exonEnds"]])
        self.score = self._colOrNone(row, dbColIdxMap, "score", int)
        self.name2 = self._colOrNone(row, dbColIdxMap, "name2", str)
        self.cdsStartStat = self._colOrNone(row, dbColIdxMap, "cdsStartStat", CdsStat)
        self.cdsEndStat = self._colOrNone(row, dbColIdxMap, "cdsEndStat", CdsStat)
        exonFrames = self._colOrNone(row, dbColIdxMap, "exonFrames", intArraySplit)
        self.hasExonFrames = (exonFrames is not None)
        self._buildExons(exonStarts, exonEnds, exonFrames)

    def _initEmpty(self):
        self.name = None
        self.chrom = None
        self.strand = None
        self.strandRel = False    # are these strand-relative coordinates
        self.txStart = None
        self.txEnd = None
        self.cdsStart = None
        self.cdsEnd = None
        self.score = None
        self.name2 = None
        self.cdsStartStat = None
        self.cdsEndStat = None
        self.hasExonFrames = False
        self.exons = []
        self.cdsStartIExon = None
        self.cdsEndIExon = None

    def _initClone(self, gp):
        self.name = gp.name
        self.chrom = gp.chrom
        self.strand = gp.strand
        self.strandRel = gp.strandRel
        self.txStart = gp.txStart
        self.txEnd = gp.txEnd
        self.cdsStart = gp.cdsStart
        self.cdsEnd = gp.cdsEnd
        self.score = gp.score
        self.name2 = gp.name2
        self.cdsStartStat = gp.cdsStartStat
        self.cdsEndStat = gp.cdsEndStat
        self.hasExonFrames = gp.hasExonFrames
        self.exons = copy.deepcopy(gp.exons)
        self.cdsStartIExon = gp.cdsStartIExon
        self.cdsEndIExon = gp.cdsEndIExon

    def _initSwapToOtherStrand(self, gp, chromSize):
        "swap coordinates to other strand"
        self.name = gp.name
        self.chrom = gp.chrom
        self.strand = gp.strand
        self.strandRel = True
        self.txStart = chromSize - gp.txEnd
        self.txEnd = chromSize - gp.txStart
        self.cdsStart = chromSize - gp.cdsEnd
        self.cdsEnd = chromSize - gp.cdsStart
        self.score = gp.score
        self.name2 = gp.name2
        self.cdsStartStat = gp.cdsEndStat
        self.cdsEndStat = gp.cdsStartStat
        self.hasExonFrames = gp.hasExonFrames
        self.exons = []
        self.cdsStartIExon = None
        self.cdsEndIExon = None
        for exon in reversed(gp.exons):
            self.addExon(chromSize - exon.end, chromSize - exon.start, exon.frame)

    def __init__(self, row=None, dbColIdxMap=None, noInitialize=False):
        "If row is not None, parse a row, otherwise initialize to empty state"
        if dbColIdxMap is not None:
            self._initDb(row, dbColIdxMap)
        elif row is not None:
            self._initParse(row)
        elif not noInitialize:
            self._initEmpty()

    def getStrandRelative(self, chromSize):
        """create a copy of this GenePred object that has strand relative
        coordinates."""
        gp = GenePred(noInitialize=True)
        if self.inDirectionOfTranscription():
            gp._initClone(self)
            gp.strandRel = True
        else:
            gp._initSwapToOtherStrand(self, chromSize)
        return gp

    def inDirectionOfTranscription(self):
        "are exons in the direction of transcriptions"
        return (self.strand == "+") or self.strandRel

    def _overlapsCds(self, exonStart, exonEnd):
        return (self.cdsStart is not None) and (self.cdsStart < self.cdsEnd) and (exonStart < self.cdsEnd) and (exonEnd > self.cdsStart)

    def addExon(self, exonStart, exonEnd, frame=None):
        "add an exon; which must be done in assending order"
        i = len(self.exons)
        self.exons.append(Exon(self, i, exonStart, exonEnd, frame))
        if self._overlapsCds(exonStart, exonEnd):
            if self.cdsStartIExon is None:
                self.cdsStartIExon = i
            self.cdsEndIExon = i

    def assignFrames(self):
        "set frames on exons, assuming no frame shift"
        if self.inDirectionOfTranscription():
            iStart = 0
            iEnd = len(self.exons)
            iDir = 1
        else:
            iStart = len(self.exons) - 1
            iEnd = -1
            iDir = -1
        cdsOff = 0
        for i in range(iStart, iEnd, iDir):
            e = self.exons[i]
            c = e.getCds()
            if c is not None:
                e.frame = cdsOff % 3
                cdsOff += (c.end - c.start)
            else:
                e.frame = -1
        self.hasExonFrames = True

    def overlaps(self, start, end):
        "test if a range overlaps the gene range"
        return (start < self.txEnd) and (end > self.txStart)

    def inCds(self, pos):
        "test if a position is in the CDS"
        return (self.cdsStart <= pos) and (pos < self.cdsEnd)

    def overlapsCds(self, startOrRange, end=None):
        "test if a position is in the CDS. startOrRange is a Range or Exon if end is None"
        if end is None:
            return (startOrRange.start < self.cdsEnd) and (startOrRange.end > self.cdsStart)
        else:
            return (startOrRange < self.cdsEnd) and (end > self.cdsStart)

    def sameCds(self, gene2):
        "test if another gene has the same CDS as this gene"
        if id(self) == id(gene2):
            return True  # same object
        if (gene2.chrom != self.chrom) or (gene2.strand != self.strand) or (gene2.cdsStart != self.cdsStart) or (gene2.cdsEnd != self.cdsEnd):
            return False
        nCds1 = self.getNumCdsExons()
        nCds2 = gene2.getNumCdsExons()
        if (nCds1 != nCds2):
            return False

        # check each exon
        checkFrame = self.hasExonFrames and gene2.hasExonFrames
        iCds2 = 0
        for iCds1 in range(nCds1):
            exon1 = self.getCdsExon(iCds1)
            exon2 = gene2.getCdsExon(iCds2)
            if exon1.getCds() != exon2.getCds():
                return False
            if checkFrame and (exon1.frame != exon2.frame):
                return False
            iCds2 += 1
        return True

    def hasCds(self):
        return (self.cdsStartIExon is not None)

    def getCds(self):
        "get Range of CDS, or None if there isn't any"
        if self.cdsStart < self.cdsEnd:
            return Range(self.cdsStart, self.cdsEnd)
        else:
            return None

    def getLenExons(self):
        "get the total length of all exons"
        bases = 0
        for e in self.exons:
            bases += e.size()
        return bases

    def getLenCds(self):
        "get the total length of CDS"
        bases = 0
        for e in self.exons:
            cds = e.getCds()
            if cds is not None:
                bases += cds.end - cds.start
        return bases

    def getSpan(self):
        "get the genomic span (txStart to txEnd length)"
        return self.txEnd - self.txStart

    def getNumCdsExons(self):
        "get the number of exons containing CDS"
        if self.cdsStartIExon is None:
            return 0
        else:
            return (self.cdsEndIExon - self.cdsStartIExon) + 1

    def getCdsExon(self, iCdsExon):
        "get a exon containing CDS, by CDS exon index"
        return self.exons[self.cdsStartIExon + iCdsExon]

    def getSortedExonIndexes(self):
        "generator for exon indexes sorted in order of transcription"
        if self.inDirectionOfTranscription():
            return list(range(0, len(self.exons), 1))
        else:
            return list(range(len(self.exons) - 1, -1, -1))

    def getSortedExons(self):
        "get list of exons, sorted in order of transcription."
        if self.inDirectionOfTranscription():
            return list(self.exons)
        else:
            return [self.exons[i] for i in range(len(self.exons) - 1, -1, -1)]

    def getRow(self):
        # FIXME standardize on getRow or Psl.toRow
        row = [self.name, self.chrom, self.strand, str(self.txStart), str(self.txEnd), str(self.cdsStart), str(self.cdsEnd)]
        row.append(str(len(self.exons)))
        starts = []
        ends = []
        for e in self.exons:
            starts.append(e.start)
            ends.append(e.end)
        row.append(intArrayJoin(starts))
        row.append(intArrayJoin(ends))

        hasExt = (self.score is not None) or (self.name2 is not None) or (self.cdsStartStat is not None) or self.hasExonFrames

        if self.score is not None:
            row.append(str(self.score))
        elif hasExt:
            row.append("0")
        if self.name2 is not None:
            row.append(self.name2)
        elif hasExt:
            row.append("")
        if self.cdsStartStat is not None:
            row.append(str(self.cdsStartStat))
            row.append(str(self.cdsEndStat))
        elif hasExt:
            row.append(str(CdsStat.unknown))
            row.append(str(CdsStat.unknown))
        if self.hasExonFrames or hasExt:
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
        for exon in self.exons:
            if exon.contains(pos):
                return exon
        return None

    def overlapAmt(self, gp2):
        "count exon bases that overlap"
        if (self.chrom != gp2.chrom) or (self.strand != gp2.strand):
            return 0
        cnt = 0
        for e1 in self.exons:
            for e2 in gp2.exons:
                cnt += e1.overlapAmt(e2.start, e2.end)
        return cnt

    def similarity(self, gp2):
        "compute similariy of two genes"
        overCnt = self.overlapAmt(gp2)
        if overCnt == 0:
            return 0.0
        else:
            return (2 * overCnt) / (self.getLenExons() + gp2.getLenExons())

    def cdsOverlapAmt(self, gp2):
        "count cds bases that overlap"
        if (self.chrom != gp2.chrom) or (self.strand != gp2.strand):
            return 0
        feats2 = gp2.getFeatures()
        cnt = 0
        for e1 in self.exons:
            f1 = e1.featureSplit()
            if f1.cds is not None:
                for f2 in feats2:
                    if f2.cds is not None:
                        cnt += f1.cds.overlapAmt(f2.cds)
        return cnt

    def cdsSimilarity(self, gp2):
        "compute similariy of CDS of two genes"
        overCnt = self.cdsOverlapAmt(gp2)
        if overCnt == 0:
            return 0.0
        else:
            return (2 * overCnt) / (self.getLenCds() + gp2.getLenCds())

    def cdsCover(self, gp2):
        "compute faction of CDS is covered a gene"
        overCnt = self.cdsOverlapAmt(gp2)
        if overCnt == 0:
            return 0.0
        else:
            return overCnt / self.getLenCds()

    def __str__(self):
        return "\t".join(self.getRow())

    def write(self, fh):
        fh.write(str(self))
        fh.write("\n")


class GenePredTbl(list):
    """Table of GenePred objects loaded from a tab-file"""
    def __init__(self, fileName, buildIdx=False, buildUniqIdx=False, buildRangeIdx=False):
        if buildIdx and buildUniqIdx:
            raise PycbioException("can't specify both buildIdx and buildUniqIdx")
        for row in GenePredReader(fileName):
            self.append(row)
        self.names = None
        self.rangeMap = None
        if buildUniqIdx:
            self._buildUniqIdx()
        if buildIdx:
            self._buildIdx()
        if buildRangeIdx:
            self._buildRangeIdx()

    def _buildUniqIdx(self):
        self.names = dict()
        for row in self:
            if row.name in self.names:
                raise PycbioException("gene with this name already in index: " + row.name)
            self.names[row.name] = row

    def _buildIdx(self):
        self.names = defaultdict(list)
        for row in self:
            self.names.append(row.name, row)

    def _buildRangeIdx(self):
        from pycbio.hgdata.RangeFinder import RangeFinder
        self.rangeMap = RangeFinder()
        for gene in self:
            self.rangeMap.add(gene.chrom, gene.txStart, gene.txEnd, gene, gene.strand)


def GenePredReader(fspec):
    """Read genePreds from a tab file which maybe specified as
    a file name or a file-like object"""
    for gp in TabFileReader(fspec, rowClass=GenePred, hashAreComments=True, skipBlankLines=True):
        yield gp
