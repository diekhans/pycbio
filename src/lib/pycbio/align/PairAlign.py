"""
Pairwise alignment or an annotation
"""
import sys,copy,re
from pycbio.sys.Enumeration import Enumeration
from pycbio.hgdata.Psl import PslReader
from pycbio.hgdata.Frame import frameIncr,frameToPhase
from pycbio.sys.fileOps import prLine,iterLines
#from Bio.Seq import reverse_complement,translate

class Seq(object):
    "Sequence in an alignment, coordinates are strand-specific"
    __slots__ = ("id", "start", "end", "size", "strand", "cds")
    def __init__(self, id, start, end, size, strand, cds=None):
        self.id = id
        self.start = start
        self.end = end
        self.size = size
        self.strand = strand
        self.cds = cds

    def revCmpl(self):
        "return a reverse complment of this object"
        cds = self.cds.revCmpl(self.size) if self.cds != None else None
        strand = '-' if (self.strand == '+') else '+'
        return Seq(self.id, self.size-self.end, self.size-self.start, self.size, strand, cds)

    def __str__(self):
        return self.id + ":" + str(self.start) + "-" + str(self.end) + "/" \
            + self.strand + " sz: " + str(self.size) + " cds: " + str(self.cds)

    def __len__(self):
        "get sequence length"
        return self.end-self.start
    
class SubSeq(object):
    "subsequence in alignment"
    __slots__ = ("seq", "start", "end", "cds")
    def __init__(self, seq, start, end, cds=None):
        self.seq = seq
        self.start = start
        self.end = end
        self.cds = cds

    def __str__(self):
        return str(self.start) + "-" + str(self.end) \
            + ((" cds: " + str(self.cds)) if (self.cds != None) else "")

    def revCmpl(self, revSeq):
        "return a reverse complment of this object for revSeq"
        cds = self.cds.revCmpl(revSeq.size) if self.cds != None else None
        return SubSeq(revSeq, revSeq.size-self.end, revSeq.size-self.start, cds)

    def __len__(self):
        "get sequence length"
        return self.end-self.start
    
class Cds(object):
    "range or subrange of CDS"
    __slots__ = ("start", "end")
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def revCmpl(self, psize):
        "return a reverse complment of this object, given parent seq or subseq size"
        return Cds(psize-self.end, psize-self.start)

    def __str__(self):
        return str(self.start) + "-" + str(self.end)
        
    def __len__(self):
        "get CDS length"
        return self.end-self.start
    
class Block(object):
    "block in alignment, query or target SubSeq can be None "
    __slots__ = ("q", "t")
    def __init__(self, q, t):
        assert((q == None) or (t == None) or (len(q) == len(t)))
        self.q = q
        self.t = t

    def dump(self, fh):
        "print content to file"
        prLine(fh, "\tquery:  ", self.q)
        prLine(fh, "\ttarget: ", self.t)

class PairAlign(list):
    """List of alignment blocks"""
    def __init__(self, qseq, tseq, cds=None):
        self.qseq = qseq
        self.tseq = tseq

    def addBlk(self, q, t):
        blk = Block(q, t)
        self.append(blk)
        return blk

    def revCmpl(self):
        "return a reverse complment of this object"
        qseq = self.qseq.revCmpl()
        tseq = self.tseq.revCmpl()
        aln = PairAlign(qseq, tseq)
        for i in xrange(len(self)-1, -1, -1):
            blk = self[i]
            aln.addBlk((None if (blk.q == None) else blk.q.revCmpl(qseq)),
                       (None if (blk.t == None) else blk.t.revCmpl(tseq)))
        return aln

    def dump(self, fh):
        "print content to file"
        prLine(fh, "query:  ", self.qseq)
        prLine(fh, "target: ", self.tseq)
        for blk in self:
            blk.dump(fh)

def _pslSeq(name, start, end, size, strand, cds=None):
    "make a seq from a PSL, reversing range is neg strand"
    if strand == '-':
        return Seq(name, size-end, size-start, size, strand, cds)
    else:
        return Seq(name, start, end, size, strand, cds)

def _getCds(cdsRange, strand, size):
    if cdsRange == None:
        return None
    cds = Cds(cdsRange[0], cdsRange[1])
    if strand == '-':
        cds = cds.revCmpl(size)
    return cds

def  _getCdsSub(cds, sub):
    "construct CDS subtrange for sequence subrange"
    st = max(cds.start, sub.start)
    en = min(cds.end, sub.end)
    if st < en:
        return Cds(st, en)
    else:
        return None

def fromPsl(psl, qCdsRange=None):
    "generate a PairAlign from a PSL. cdsRange is None or a tuple"
    qCds = _getCds(qCdsRange, psl.getQStrand(), psl.qSize)
    qseq = _pslSeq(psl.qName, psl.qStart, psl.qEnd, psl.qSize, psl.getQStrand(), qCds)
    tseq = _pslSeq(psl.tName, psl.tStart, psl.tEnd, psl.tSize, psl.getTStrand())
    aln = PairAlign(qseq, tseq)
    for i in xrange(psl.blockCount):
        blk = aln.addBlk(SubSeq(qseq, psl.qStarts[i], psl.getQEnd(i)),
                         SubSeq(tseq, psl.tStarts[i], psl.getTEnd(i)))
        if qCds != None:
            blk.q.cds = _getCdsSub(qCds, blk.q)
    return aln

class CdsTable(dict):
    """table mapping ids to tuple of zero-based (start end),
    Load from CDS seperated file in form:
       cds start..end
    """
    def __init__(self, cdsFile):
        for line in iterLines(cdsFile):
            if not line.startswith('#'):
                self.__parseCds(line)
    
    __parseRe = re.compile("^([^\t]+)\t([0-9]+)\\.\\.([0-9]+)$")
    def __parseCds(self, line):
        m = self.__parseRe.match(line)
        if m == None:
            raise Exception("can't parse CDS line: " + line)
        st = int(m.group(2))-1
        en = int(m.group(3))-1
        self[m.group(1)] = (st, en)

def loadPslFile(pslFile, cdsFile=None):
    "build list of PairAlign from a PSL file and optional CDS file"
    cdsTbl = CdsTable(cdsFile) if (cdsFile != None) else {}
    alns = []
    for psl in PslReader(pslFile):
        alns.append(fromPsl(psl, cdsTbl.get(psl.qName)))
    return alns
