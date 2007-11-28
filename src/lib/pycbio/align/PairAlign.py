"""
Pairwise alignment.  All coordinates are strand-specific

"""
import sys,copy,re
from pycbio.sys.Enumeration import Enumeration
from pycbio.hgdata.Psl import PslReader
from pycbio.hgdata.Frame import frameIncr,frameToPhase
from pycbio.sys.fileOps import prLine,iterLines

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

    def locStr(self):
        "get string describing location"
        return self.seq.id + ":" + str(self.start) + "-" + str(self.end)
        
    def revCmpl(self, revSeq):
        "return a reverse complment of this object for revSeq"
        cds = self.cds.revCmpl(revSeq.size) if self.cds != None else None
        return SubSeq(revSeq, revSeq.size-self.end, revSeq.size-self.start, cds)

    def __len__(self):
        "get sequence length"
        return self.end-self.start

    def overlaps(self, start, end):
        "determine if subseqs overlap"
        maxStart = max(self.start, start)
        minEnd = min(self.end, end)
        return (maxStart < minEnd)
    
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
    """Block in alignment, query or target SubSeq can be None.  Links allow
    for simple traversing"""
    __slots__ = ("aln", "q", "t", "idx", "prev", "next")
    def __init__(self, aln, q, t, idx):
        assert((q == None) or (t == None) or (len(q) == len(t)))
        self.aln = aln
        self.q = q
        self.t = t
        self.idx = idx
        self.prev = self.next = None

    def __len__(self):
        "length of block"
        return len(self.q) if (self.q != None) else len(self.t)

    def __str__(self):
        return str(self.q) + " <=> " + str(self.t)

    def isAln(self):
        "is this block aligned?"
        return (self.q != None) and (self.t != None)

    def isQIns(self):
        "is this block a query insert?"
        return (self.q != None) and (self.t == None)

    def isTIns(self):
        "is this block a target insert?"
        return (self.q == None) and (self.t != None)

    def __subToRow(self, seq, sub):
        if sub != None:
            return [seq.id, sub.start, sub.end]
        else:
            return [seq.id, None, None]

    def toRow(self):
        "convert to list of query and target coords"
        return  self.__subToRow(self.aln.qseq, self.q) + self.__subToRow(self.aln.tseq, self.t)

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
        blk = Block(self, q, t, len(self))
        if len(self) > 0:
            self[-1].next = blk
            blk.prev = self[-1]
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

    def anyTOverlap(self, other):
        "determine if the any target blocks overlap"
        if (self.tseq.id != other.tseq.id) or (self.tseq.strand != other.tseq.strand):
            return False
        oblk = other[0]
        for blk in self:
            if blk.isAln():
                while oblk != None:
                    if oblk.isAln():
                        if oblk.t.start > blk.t.end:
                            return False
                        elif blk.t.overlaps(oblk.t.start, oblk.t.end):
                            return True
                    oblk = oblk.next
            if oblk == None:
                break
        return False

    def dump(self, fh):
        "print content to file"
        prLine(fh, "query:  ", self.qseq)
        prLine(fh, "target: ", self.tseq)
        for blk in self:
            blk.dump(fh)


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

def _mkPslSeq(name, start, end, size, strand, cds=None):
    "make a seq from a PSL q or t, reversing range is neg strand"
    if strand == '-':
        return Seq(name, size-end, size-start, size, strand, cds)
    else:
        return Seq(name, start, end, size, strand, cds)

def _addPslBlk(psl, aln, qCds, i, prevBlk, inclUnaln):
    """add an aligned block, and optionally preceeding unaligned blocks"""
    qStart = psl.qStarts[i]
    qEnd = psl.getQEnd(i)
    tStart = psl.tStarts[i]
    tEnd = psl.getTEnd(i)
    if inclUnaln and (i > 0):
        if qStart > prevBlk.q.end:
            blk = aln.addBlk(SubSeq(aln.qseq, prevBlk.q.end, qStart), None)
            if qCds != None:
                blk.q.cds = _getCdsSub(qCds, blk.q)
        if tStart > prevBlk.t.end:
            blk = aln.addBlk(None, SubSeq(aln.tseq, prevBlk.t.end, tStart))
    blk = aln.addBlk(SubSeq(aln.qseq, qStart, qEnd),
                     SubSeq(aln.tseq, tStart, tEnd))
    if qCds != None:
        blk.q.cds = _getCdsSub(qCds, blk.q)
    return blk

def fromPsl(psl, qCdsRange=None, inclUnaln=False):
    """generate a PairAlign from a PSL. cdsRange is None or a tuple. In
    inclUnaln is True, then include Block objects for unaligned regions"""
    qCds = _getCds(qCdsRange, psl.getQStrand(), psl.qSize)
    qseq = _mkPslSeq(psl.qName, psl.qStart, psl.qEnd, psl.qSize, psl.getQStrand(), qCds)
    tseq = _mkPslSeq(psl.tName, psl.tStart, psl.tEnd, psl.tSize, psl.getTStrand())
    aln = PairAlign(qseq, tseq)
    prevBlk = None
    for i in xrange(psl.blockCount):
        prevBlk = _addPslBlk(psl, aln, qCds, i, prevBlk, inclUnaln)
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

def loadPslFile(pslFile, cdsFile=None, inclUnaln=False):
    "build list of PairAlign from a PSL file and optional CDS file"
    cdsTbl = CdsTable(cdsFile) if (cdsFile != None) else {}
    alns = []
    for psl in PslReader(pslFile):
        alns.append(fromPsl(psl, cdsTbl.get(psl.qName), inclUnaln))
    return alns
