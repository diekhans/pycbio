# Copyright 2006-2022 Mark Diekhans
import copy
from collections import defaultdict, namedtuple
from pycbio.tsv.tabFile import TabFileReader
from pycbio.hgdata.autoSql import intArraySplit, intArrayJoin
from pycbio.hgdata.frame import Frame
from pycbio.sys.symEnum import SymEnum, SymEnumValue
from pycbio import PycbioException


# FIXME range and exon overlap functions are inconsistent.  exon should inherit from range.
# FIXME: ExonFeatures should use Range
# FIXME needs many more tests
# FIXME: should use from pycbio.hgdata.frame import Frame


class CdsStat(SymEnum):
    none = SymEnumValue("none", "none")                # No CDS (non-coding)
    unknown = SymEnumValue("unknown", "unk")           # CDS is unknown (coding, but not known)
    incomplete = SymEnumValue("incomplete", "incmpl")  # CDS is not complete at this end
    complete = SymEnumValue("complete", "cmpl")        # CDS is complete at this end


# these are ordered for accessing tab files
genePredColumns = ("name", "chrom", "strand", "txStart", "txEnd", "cdsStart", "cdsEnd", "exonCount", "exonStarts", "exonEnds")
genePredExtColumns = genePredColumns + ("score", "name2", "cdsStartStat", "cdsEndStat", "exonFrames")
genePredExt2Columns = genePredExtColumns + ("type", "geneName", "geneName2", "geneType")
bigGenePredColumns = ("chrom", "chromStart", "chromEnd", "name", "score", "strand", "thickStart",
                      "thickEnd", "reserved", "blockCount", "blockSizes", "chromStarts", "name2",
                      "cdsStartStat", "cdsEndStat", "exonFrames", "type", "geneName", "geneName2", "geneType",)


class Range(namedtuple("Range", ("start", "end"))):
    "start and end coordinates"
    __slots__ = ()
    # FIXME: maybe base class for coords?

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
        return str(self.start) + "-" + str(self.end)

    def reverse(self, chromSize):
        "get a range on the opposite strand"
        return Range(chromSize - self.end, chromSize - self.start)


class ExonFeatures(namedtuple("ExonFeatures", ("utr5", "cds", "utr3"))):
    "Object the holds the features of a single exon as Range objects or None"
    __slots__ = ()
    pass

class Exon:
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
        """split exon into an object with the fields (utr5, cds, utr3)
`        where each element is either None, or (start, end).  utr5 is 5' UTR
        in the exon, utr3, is 3'UTR, and cds is coding sequence of the exon."""

        utr5 = cds = utr3 = None

        # UTR before CDS in exon
        start = self.start
        if (start < self.gene.cdsStart):
            end = min(self.end, self.gene.cdsStart)
            if self.gene.inDirectionOfTranscription():
                utr5 = Range(start, end)
            else:
                utr3 = Range(start, end)
            start = end

        # CDS in exon
        if (start < self.end) and (start < self.gene.cdsEnd):
            end = min(self.end, self.gene.cdsEnd)
            cds = Range(start, end)
            start = end

        # UTR after CDS in exon
        if (start < self.end) and (start >= self.gene.cdsEnd):
            if self.gene.inDirectionOfTranscription():
                utr3 = Range(start, self.end)
            else:
                utr5 = Range(start, self.end)

        return ExonFeatures(utr5, cds, utr3)


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

    def __len__(self):
        "size of the exon"
        return self.end - self.start

    def getRelCoords(self, chromSize):
        "get a range object of strand-relative coordinates"
        if self.gene.inDirectionOfTranscription():
            return Range(self.start, self.end)
        else:
            return Range(chromSize - self.end, chromSize - self.start)


class GenePred:
    """Object wrapper for a genePred"""

    def __init__(self, name=None, chrom=None, strand=None, txStart=None, txEnd=None, cdsStart=None, cdsEnd=None):
        self.name = name
        self.chrom = chrom
        self.strand = strand
        self.txStart = txStart
        self.txEnd = txEnd
        self.cdsStart = cdsStart
        self.cdsEnd = cdsEnd
        self.exons = []
        self.score = None
        self.name2 = None
        self.cdsStartStat = None
        self.cdsEndStat = None
        self.hasExonFrames = False
        self.cdsStartIExon = None
        self.cdsEndIExon = None
        self.strandRel = False    # are these strand-relative coordinates?

    def clone(self):
        "name a copy"
        return copy.deepcopy(self)

    def _cloneToOtherStrand(self, chromSize):
        "swap coordinates to other strand"
        gp = copy.copy(self)
        gp.txStart = chromSize - self.txEnd
        gp.txEnd = chromSize - self.txStart
        gp.cdsStart = chromSize - self.cdsEnd
        gp.cdsEnd = chromSize - self.cdsStart
        gp.cdsStartIExon = gp.cdsEndIExon = None
        gp.exons = []
        for exon in reversed(self.exons):
            gp.addExon(chromSize - exon.end, chromSize - exon.start, exon.frame)
        return gp

    def getStrandRelative(self, chromSize):
        """create a copy of this GenePred object that has strand relative
        coordinates."""
        if self.inDirectionOfTranscription():
            gp = self.clone()
        else:
            gp = self._cloneToOtherStrand(chromSize)
        gp.strandRel = True
        return gp

    def inDirectionOfTranscription(self):
        "are exons in the direction of transcriptions"
        return (self.strand == "+") or self.strandRel

    def _overlapsCds(self, exonStart, exonEnd):
        return (self.cdsStart is not None) and (self.cdsStart < self.cdsEnd) and (exonStart < self.cdsEnd) and (exonEnd > self.cdsStart)

    def addExon(self, exonStart, exonEnd, frame=None):
        "add an exon; which must be done in assending order"
        i = len(self.exons)
        self.exons.append(Exon(self, i, exonStart, exonEnd, Frame(frame)))
        if self._overlapsCds(exonStart, exonEnd):
            if self.cdsStartIExon is None:
                self.cdsStartIExon = i
            self.cdsEndIExon = i
        return self.exons[-1]

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

def _buildExons(gp, exonStarts, exonEnds, exonFrames):
    "build array of exon objects"
    frame = None
    gp.cdsStartIExon = None
    gp.cdsEndIExon = None
    for i in range(len(exonStarts)):
        if exonFrames is not None:
            frame = exonFrames[i]
        gp.addExon(exonStarts[i], exonEnds[i], frame)

def genePredFromRow(row):
    "create a GenePred object from a row in a genePred file"
    gp = GenePred(row[0], row[1], row[2], int(row[3]), int(row[4]), int(row[5]), int(row[6]))
    exonStarts = intArraySplit(row[8])
    exonEnds = intArraySplit(row[9])
    iCol = 10
    numCols = len(row)
    gp.score = None
    if iCol < numCols:  # 10
        gp.score = int(row[iCol])
        iCol = iCol + 1
    gp.name2 = None
    if iCol < numCols:  # 11
        gp.name2 = row[iCol]
        iCol = iCol + 1
    gp.cdsStartStat = None
    gp.cdsEndStat = None
    if iCol < numCols:  # 12,13
        gp.cdsStartStat = CdsStat(row[iCol])
        gp.cdsEndStat = CdsStat(row[iCol + 1])
        iCol = iCol + 2
    exonFrames = None
    gp.hasExonFrames = False
    if iCol < numCols:  # 14
        exonFrames = intArraySplit(row[iCol])
        iCol = iCol + 1
        gp.hasExonFrames = True
    _buildExons(gp, exonStarts, exonEnds, exonFrames)
    return gp

def _colOrNone(rec, colName, typeCnv):
    val = rec.get(colName)
    return None if (val is None) else typeCnv(val)

def genePredFromDict(rec):
    "create a GenePred object from a rec that is a dictionary, often from a database"
    gp = GenePred(rec["name"], rec["chrom"], rec["strand"],
                  int(rec["txStart"]), int(rec["txEnd"]),
                  int(rec["cdsStart"]), int(rec["cdsEnd"]))
    exonStarts = intArraySplit(rec["exonStarts"])
    exonEnds = intArraySplit(rec["exonEnds"])

    # this are genePredExt columns
    gp.score = _colOrNone(rec, "score", int)
    gp.name2 = _colOrNone(rec, "name2", str)
    gp.cdsStartStat = _colOrNone(rec, "cdsStartStat", CdsStat)
    gp.cdsEndStat = _colOrNone(rec, "cdsEndStat", CdsStat)
    exonFrames = _colOrNone(rec, "exonFrames", intArraySplit)
    gp.hasExonFrames = (exonFrames is not None)
    _buildExons(gp, exonStarts, exonEnds, exonFrames)
    return gp

def genePredFromBigGenePred(row):
    """Reimplementation of kent/src/hg/lib/genePred.c to convert bigGenePred row to genePred.
    This simplifies readings, as bigGenePredToGenePred doesn't return extra columns that are
    needed.
    """
    # chrom	chromStart	chromEnd	name	score	strand	thickStart	thickEnd	reserved	blockCount	blockSizes	chromStarts	name2	cdsStartStat	cdsEndStat	exonFrames
    gp = GenePred(row[3], row[0], row[5], int(row[1]), int(row[2]), int(row[6]), int(row[7]))
    blockSizes = intArraySplit(row[10])
    blockStarts = intArraySplit(row[11])
    gp.name2 = row[12]
    gp.cdsStartStat = row[13]
    gp.cdsEndStat = row[14]
    exonFrames = intArraySplit(row[15])
    gp.hasExonFrames = (exonFrames is not None)
    chromStart = gp.txStart
    for i in range(len(blockSizes)):
        start = blockStarts[i] + chromStart
        gp.addExon(start, start + blockSizes[i], exonFrames[i])
    return gp


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
    for gp in TabFileReader(fspec, rowClass=lambda row: genePredFromRow(row),
                            hashAreComments=True, skipBlankLines=True):
        yield gp
