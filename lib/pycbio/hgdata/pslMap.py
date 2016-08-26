# Copyright 2006-2012 Mark Diekhans

class PslMapRange(object):
    """A subrange of requested mapping, which is either aligned on unaligned.
    If aligned both query and target ranges are set, if unaligned only one.
    prev/next coordinates are only set when corresponding range is not set (unaligned).
    """
    __slots__ = ("qPrevEnd", "qStart", "qEnd", "qNextStart", "tPrevEnd", "tStart", "tEnd", "tNextStart")
    def __init__(self, qPrevEnd, qStart, qEnd,  qNextStart, tPrevEnd, tStart, tEnd, tNextStart):
        self.qPrevEnd = qPrevEnd
        self.qStart = qStart
        self.qEnd = qEnd
        self.qNextStart = qNextStart
        self.tPrevEnd = tPrevEnd
        self.tStart = tStart
        self.tEnd = tEnd
        self.tNextStart = tNextStart

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

    def __t2qProcessGap(self, prevBlk, nextBlk, tRngNext, tRngEnd):
        """analyze  gap before blk, return updated tRngNext"""
        gapTStart = prevBlk.tEnd
        gapTEnd = nextBlk.tStart
        if tRngNext >= gapTEnd:
            return tRngNext, None  # gap before range
        assert(tRngNext >= gapTStart)
        tRngNextNext = tRngEnd if (tRngEnd < gapTEnd) else gapTEnd
        pmr = PslMapRange(prevBlk.qEnd, None, None, nextBlk.qStart,
                          None, tRngNext, tRngNextNext, None)
        return tRngNextNext, pmr

    def __t2qProcessBlk(self, blk, tRngNext, tRngEnd):
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
        pmr = PslMapRange(None, qRngNext, qRngNextNext, None,
                          None, tRngNext, tRngNextNext, None)
        return tRngNextNext, pmr

    def targetToQueryMap(self, tRngStart, tRngEnd):
        """Generator map a target range to query ranges using a PSL. Target range must
        be in PSL block-specific coordinates (positive or negative strand)"""
        # deal with gap at beginning
        tRngNext = tRngStart
        if tRngNext < self.mapPsl.blocks[0].tStart:
            yield PslMapRange(None, None, None, self.mapPsl.blocks[0].qStart,
                              None, tRngNext, self.mapPsl.blocks[0].tStart, None)
            tRngNext = self.mapPsl.blocks[0].tStart

        # process blocks and gaps
        prevBlk = None
        for blk in self.mapPsl.blocks:
            if tRngNext >= tRngEnd:
                break
            if prevBlk is not None:
                tRngNext, pmr = self.__t2qProcessGap(prevBlk, blk, tRngNext, tRngEnd)
                if pmr is not None:
                    yield pmr
            if tRngNext < tRngEnd:
                tRngNext, pmr = self.__t2qProcessBlk(blk, tRngNext, tRngEnd)
                if pmr is not None:
                    yield pmr
            prevBlk = blk

        # deal with gap at end
        lastBlk = self.mapPsl.blocks[self.mapPsl.blockCount - 1]
        if tRngEnd > lastBlk.tEnd:
            yield PslMapRange(lastBlk.qEnd, None, None, None,
                              None, lastBlk.tEnd, tRngEnd, None)

    def __q2tProcessGap(self, prevBlk, nextBlk, qRngNext, qRngEnd):
        """analyze gap before blk, return updated qRngNext"""
        gapQStart = prevBlk.qEnd
        gapQEnd = nextBlk.qStart
        if qRngNext >= gapQEnd:
            return qRngNext, None  # gap before range
        assert(qRngNext >= gapQStart)
        qRngNextNext = qRngEnd if (qRngEnd < gapQEnd) else gapQEnd
        pmr = PslMapRange(None, qRngNext, qRngNextNext, None,
                          prevBlk.tEnd, None, None, nextBlk.tStart)
        return qRngNextNext, pmr

    def __q2tProcessBlk(self, blk, qRngNext, qRngEnd):
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
        pmr = PslMapRange(None, qRngNext, qRngNextNext, None,
                          None, tRngNext, tRngNextNext, None)
        return qRngNextNext, pmr

    def queryToTargetMap(self, qRngStart, qRngEnd):
        """Map a query range to target ranges using a PSL.  Query range must
        be in PSL block-specific coordinates (positive or negative strand)"""
        # deal with gap at beginning
        qRngNext = qRngStart
        if qRngNext < self.mapPsl.blocks[0].qStart:
            yield PslMapRange(None, qRngNext, self.mapPsl.blocks[0].qStart, None,
                              None, None, None, self.mapPsl.blocks[0].tStart)
            qRngNext = self.mapPsl.blocks[0].qStart

        # process blocks and gaps
        prevBlk = None
        for blk in self.mapPsl.blocks:
            if qRngNext >= qRngEnd:
                break
            if prevBlk is not None:
                qRngNext, pmr = self.__q2tProcessGap(prevBlk, blk, qRngNext, qRngEnd)
                if pmr is not None:
                    yield pmr
            if qRngNext < qRngEnd:
                qRngNext, pmr = self.__q2tProcessBlk(blk, qRngNext, qRngEnd)
                if pmr is not None:
                    yield pmr
            prevBlk = blk

        # deal with gap at end
        lastBlk = self.mapPsl.blocks[self.mapPsl.blockCount - 1]
        if qRngEnd > lastBlk.qEnd:
            yield PslMapRange(None, lastBlk.qEnd, qRngEnd, None,
                              lastBlk.tEnd, None, None, None)
