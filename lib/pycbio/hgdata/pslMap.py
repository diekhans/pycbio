# Copyright 2006-2016 Mark Diekhans

def _reverseRange(start, end, size):
    "reverse range, if start or end is None, return that value swapped but None"
    return (size-end if end is not None else None,
            size-start if start is not None else None)

class PslMapRange(object):
    """A subrange of requested mapping, which is either aligned on unaligned.
    If aligned both query and target ranges are set, if unaligned only one.
    prev/next coordinates are only set when corresponding range is not set (unaligned).
    """
    __slots__ = ("qPrevEnd", "qStart", "qEnd", "qNextStart", "qStrand",
                 "tPrevEnd", "tStart", "tEnd", "tNextStart", "tStrand")
    def __init__(self, qPrevEnd, qStart, qEnd, qNextStart, qStrand,
                 tPrevEnd, tStart, tEnd, tNextStart, tStrand):
        self.qPrevEnd = qPrevEnd
        self.qStart = qStart
        self.qEnd = qEnd
        self.qStrand = qStrand
        self.qNextStart = qNextStart
        self.tPrevEnd = tPrevEnd
        self.tStart = tStart
        self.tEnd = tEnd
        self.tStrand = tStrand
        self.tNextStart = tNextStart

    def __len__(self):
        return (self.tEnd - self.tStart) if (self.tStart is not None) else (self.qEnd - self.qStart)
        
    def __str__(self):
        strs = []
        for s in self.__slots__:
            strs.append(str(getattr(self, s)))
        return " ".join(strs)
        
    def __eq__(self, other):
        if not isinstance(other, PslMapRange):
            return False
        for s in self.__slots__:
            if getattr(self, s) != getattr(other, s):
                return False
        return True

    def __ne__(self, other):
        return not (self == other)
        
class PslMap(object):
    """Object for mapping coordinates using PSL alignments.
    Can map from either query-to-target or target-to-query coordinates.
    Has a generator that is used to traverse the range.
    Takes an object that has the following callback functions that are
    Blocks are traversed in order, reverse complement PSL to traverse in
    opposite order.
    """
    def __init__(self, mapPsl):
        "initialize with mapping PSL"
        self.mapPsl = mapPsl

    def __mkMapRange(self, qPrevEnd, qStart, qEnd, qNextStart, qStrand,
                     tPrevEnd, tStart, tEnd, tNextStart, tStrand):
        """construct a new PslMapRange object"""
        if qStrand != self.mapPsl.getQStrand():
            qPrevEnd, qNextStart = _reverseRange(qPrevEnd, qNextStart, self.mapPsl.qSize)
            qStart, qEnd = _reverseRange(qStart, qEnd, self.mapPsl.qSize)
        if tStrand != self.mapPsl.getTStrand():
            tPrevEnd, tNextStart = _reverseRange(tPrevEnd, tNextStart, self.mapPsl.tSize)
            tStart, tEnd = _reverseRange(tStart, tEnd, self.mapPsl.tSize)
        return PslMapRange(qPrevEnd, qStart, qEnd, qNextStart, qStrand,
                           tPrevEnd, tStart, tEnd, tNextStart, tStrand)
        
    def __t2qProcessGap(self, prevBlk, nextBlk, tRngNext, tRngEnd, qStrand, tStrand):
        """analyze gap before blk, return updated tRngNext"""
        gapTStart = prevBlk.tEnd
        gapTEnd = nextBlk.tStart
        if tRngNext >= gapTEnd:
            return tRngNext, None  # gap before range
        assert(tRngNext >= gapTStart)
        tRngNextNext = tRngEnd if (tRngEnd < gapTEnd) else gapTEnd
        pmr = self.__mkMapRange(prevBlk.qEnd, None, None, nextBlk.qStart, qStrand,
                                None, tRngNext, tRngNextNext, None, tStrand)
        return tRngNextNext, pmr

    def __t2qProcessBlk(self, blk, tRngNext, tRngEnd, qStrand, tStrand):
        """Analyze next block overlapping range.  Return updated tRngNext"""
        if tRngNext >= blk.tEnd:
            return tRngNext, None  # block before range
        assert(tRngNext >= blk.tStart)

        # in this block, find corresponding query range
        qRngNext = blk.qStart + (tRngNext - blk.tStart)
        if tRngEnd < blk.tEnd:
            # ends in this block
            qRngNextNext = qRngNext + (tRngEnd - tRngNext)
            tRngNextNext = tRngEnd
        else:
            # continues after block
            left = blk.tEnd - tRngNext
            qRngNextNext = qRngNext + left
            tRngNextNext = tRngNext + left
        pmr = self.__mkMapRange(None, qRngNext, qRngNextNext, None, qStrand,
                                None, tRngNext, tRngNextNext, None, tStrand)
        return tRngNextNext, pmr

    def targetToQueryMap(self, tRngStart, tRngEnd, tStrand=None):
        """Generator map a target range to query ranges using a PSL.  If tStrand is not
        specified, target range must be match mapping PSL"""
        qStrand = self.mapPsl.getQStrand()
        if (tStrand is not None) and (tStrand != self.mapPsl.getTStrand()):
            tRngStart, tRngEnd = _reverseRange(tRngStart, tRngEnd, self.mapPsl.tSize)
        else:
            tStrand = self.mapPsl.getTStrand()

        # deal with gap at beginning
        tRngNext = tRngStart
        if tRngNext < self.mapPsl.blocks[0].tStart:
            yield self.__mkMapRange(None, None, None, self.mapPsl.blocks[0].qStart, qStrand,
                                    None, tRngNext, self.mapPsl.blocks[0].tStart, None, tStrand)
            tRngNext = self.mapPsl.blocks[0].tStart

        # process blocks and gaps
        prevBlk = None
        for blk in self.mapPsl.blocks:
            if tRngNext >= tRngEnd:
                break
            if prevBlk is not None:
                tRngNext, pmr = self.__t2qProcessGap(prevBlk, blk, tRngNext, tRngEnd, qStrand, tStrand)
                if pmr is not None:
                    yield pmr
            if tRngNext < tRngEnd:
                tRngNext, pmr = self.__t2qProcessBlk(blk, tRngNext, tRngEnd, qStrand, tStrand)
                if pmr is not None:
                    yield pmr
            prevBlk = blk

        # deal with gap at end
        lastBlk = self.mapPsl.blocks[self.mapPsl.blockCount - 1]
        if tRngEnd > lastBlk.tEnd:
            yield self.__mkMapRange(lastBlk.qEnd, None, None, None, qStrand,
                                    None, lastBlk.tEnd, tRngEnd, None, tStrand)

    def __q2tProcessGap(self, prevBlk, nextBlk, qRngNext, qRngEnd, qStrand, tStrand):
        """analyze gap before blk, return updated qRngNext"""
        gapQStart = prevBlk.qEnd
        gapQEnd = nextBlk.qStart
        if qRngNext >= gapQEnd:
            return qRngNext, None  # gap before range
        assert(qRngNext >= gapQStart)
        qRngNextNext = qRngEnd if (qRngEnd < gapQEnd) else gapQEnd
        pmr = self.__mkMapRange(None, qRngNext, qRngNextNext, None, qStrand,
                                prevBlk.tEnd, None, None, nextBlk.tStart, tStrand)
        return qRngNextNext, pmr

    def __q2tProcessBlk(self, blk, qRngNext, qRngEnd, qStrand, tStrand):
        """Analyze next block overlapping range.  Return updated qRngNext"""
        if qRngNext >= blk.qEnd:
            return qRngNext, None  # block before range
        assert(qRngNext >= blk.qStart)

        # in this block, find corresponding target range
        tRngNext = blk.tStart + (qRngNext - blk.qStart)
        if qRngEnd < blk.qEnd:
            # ends in this block
            tRngNextNext = tRngNext + (qRngEnd - qRngNext)
            qRngNextNext = qRngEnd
        else:
            # continues after block
            left = blk.qEnd - qRngNext
            tRngNextNext = tRngNext + left
            qRngNextNext = qRngNext + left
        pmr = self.__mkMapRange(None, qRngNext, qRngNextNext, None, qStrand,
                                None, tRngNext, tRngNextNext, None, tStrand)
        return qRngNextNext, pmr

    def queryToTargetMap(self, qRngStart, qRngEnd, qStrand=None):
        """Map a query range to target ranges using a PSL.  If qStrand is not
        specified, query range must be match mapping PSL"""
        if (qStrand is not None) and (qStrand != self.mapPsl.getQStrand()):
            qRngStart, qRngEnd = _reverseRange(qRngStart, qRngEnd, self.mapPsl.qSize)
        else:
            qStrand = self.mapPsl.getQStrand() 
        tStrand = self.mapPsl.getTStrand()

        # deal with gap at beginning
        qRngNext = qRngStart
        if qRngNext < self.mapPsl.blocks[0].qStart:
            yield self.__mkMapRange(None, qRngNext, self.mapPsl.blocks[0].qStart, None, qStrand,
                                    None, None, None, self.mapPsl.blocks[0].tStart, tStrand)
            qRngNext = self.mapPsl.blocks[0].qStart

        # process blocks and gaps
        prevBlk = None
        for blk in self.mapPsl.blocks:
            if qRngNext >= qRngEnd:
                break
            if prevBlk is not None:
                qRngNext, pmr = self.__q2tProcessGap(prevBlk, blk, qRngNext, qRngEnd, qStrand, tStrand)
                if pmr is not None:
                    yield pmr
            if qRngNext < qRngEnd:
                qRngNext, pmr = self.__q2tProcessBlk(blk, qRngNext, qRngEnd, qStrand, tStrand)
                if pmr is not None:
                    yield pmr
            prevBlk = blk

        # deal with gap at end
        lastBlk = self.mapPsl.blocks[self.mapPsl.blockCount - 1]
        if qRngEnd > lastBlk.qEnd:
            yield self.__mkMapRange(None, lastBlk.qEnd, qRngEnd, None, qStrand,
                                    lastBlk.tEnd, None, None, None, tStrand)
