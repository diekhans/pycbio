# Copyright 2006-2016 Mark Diekhans
from collections import namedtuple
from pycbio.hgdata.psl import Psl, PslBlock, reverseCoords


def _reverseRange(start, end, size):
    "reverse range, if start or end is None, return that value swapped but None"
    return (size - end if end is not None else None,
            size - start if start is not None else None)


class PslMapRange(namedtuple("PslMapRange",
                             ("qPrevEnd", "qStart", "qEnd", "qNextStart", "qStrand",
                              "tPrevEnd", "tStart", "tEnd", "tNextStart", "tStrand"))):
    """A subrange of requested mapping, which is either aligned on unaligned.
    If aligned both query and target ranges are set, if unaligned only one.
    prev/next coordinates are only set when corresponding range is not set (unaligned).
    """
    __slots__ = ()

    @property
    def isAligned(self):
        return (self.qStart is not None) and (self.tStart is not None)

    @property
    def isQInsert(self):
        return (self.qStart is not None) and (self.tStart is None)

    @property
    def isTInsert(self):
        return (self.qStart is None) and (self.tStart is not None)

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

    @staticmethod
    def factory(mapPsl, qPrevEnd, qStart, qEnd, qNextStart, qStrand,
                tPrevEnd, tStart, tEnd, tNextStart, tStrand):
        """construct a new PslMapRange object"""
        if qStrand != mapPsl.qStrand:
            qPrevEnd, qNextStart = _reverseRange(qPrevEnd, qNextStart, mapPsl.qSize)
            qStart, qEnd = _reverseRange(qStart, qEnd, mapPsl.qSize)
        if tStrand != mapPsl.tStrand:
            tPrevEnd, tNextStart = _reverseRange(tPrevEnd, tNextStart, mapPsl.tSize)
            tStart, tEnd = _reverseRange(tStart, tEnd, mapPsl.tSize)
        return PslMapRange(qPrevEnd, qStart, qEnd, qNextStart, qStrand,
                           tPrevEnd, tStart, tEnd, tNextStart, tStrand)


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

    def _t2qProcessGap(self, prevBlk, nextBlk, tRngNext, tRngEnd, qStrand, tStrand, handler):
        """analyze gap before blk, return updated tRngNext"""
        gapTStart = prevBlk.tEnd
        gapTEnd = nextBlk.tStart
        if tRngNext >= gapTEnd:
            return tRngNext, None  # gap before range
        assert(tRngNext >= gapTStart)
        tRngNextNext = tRngEnd if (tRngEnd < gapTEnd) else gapTEnd
        pmr = handler(self.mapPsl, prevBlk.qEnd, None, None, nextBlk.qStart, qStrand,
                      None, tRngNext, tRngNextNext, None, tStrand)
        return tRngNextNext, pmr

    def _t2qProcessBlk(self, blk, tRngNext, tRngEnd, qStrand, tStrand, handler):
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
        pmr = handler(self.mapPsl, None, qRngNext, qRngNextNext, None, qStrand,
                      None, tRngNext, tRngNextNext, None, tStrand)
        return tRngNextNext, pmr

    def targetToQueryMap(self, tRngStart, tRngEnd, tStrand=None, handler=PslMapRange.factory):
        """Generator map a target range to query ranges using a PSL.  If tStrand is not
        specified, target range must be match mapping PSL"""
        qStrand = self.mapPsl.qStrand
        if (tStrand is not None) and (tStrand != self.mapPsl.tStrand):
            tRngStart, tRngEnd = _reverseRange(tRngStart, tRngEnd, self.mapPsl.tSize)
        else:
            tStrand = self.mapPsl.tStrand

        # deal with gap at beginning
        tRngNext = tRngStart
        if tRngNext < self.mapPsl.blocks[0].tStart:
            yield handler(self.mapPsl, None, None, None, self.mapPsl.blocks[0].qStart, qStrand,
                          None, tRngNext, self.mapPsl.blocks[0].tStart, None, tStrand)
            tRngNext = self.mapPsl.blocks[0].tStart

        # process blocks and gaps
        prevBlk = None
        for blk in self.mapPsl.blocks:
            if tRngNext >= tRngEnd:
                break
            if prevBlk is not None:
                tRngNext, pmr = self._t2qProcessGap(prevBlk, blk, tRngNext, tRngEnd, qStrand, tStrand, handler)
                if pmr is not None:
                    yield pmr
            if tRngNext < tRngEnd:
                tRngNext, pmr = self._t2qProcessBlk(blk, tRngNext, tRngEnd, qStrand, tStrand, handler)
                if pmr is not None:
                    yield pmr
            prevBlk = blk

        # deal with gap at end
        lastBlk = self.mapPsl.blocks[self.mapPsl.blockCount - 1]
        if tRngEnd > lastBlk.tEnd:
            yield handler(self.mapPsl, lastBlk.qEnd, None, None, None, qStrand,
                          None, max(tRngStart, lastBlk.tEnd), tRngEnd, None, tStrand)

    def _q2tProcessGap(self, prevBlk, nextBlk, qRngNext, qRngEnd, qStrand, tStrand, handler):
        """analyze gap before blk, return updated qRngNext"""
        gapQStart = prevBlk.qEnd
        gapQEnd = nextBlk.qStart
        if qRngNext >= gapQEnd:
            return qRngNext, None  # gap before range
        assert(qRngNext >= gapQStart)
        qRngNextNext = qRngEnd if (qRngEnd < gapQEnd) else gapQEnd
        pmr = handler(self.mapPsl, None, qRngNext, qRngNextNext, None, qStrand,
                      prevBlk.tEnd, None, None, nextBlk.tStart, tStrand)
        return qRngNextNext, pmr

    def _q2tProcessBlk(self, blk, qRngNext, qRngEnd, qStrand, tStrand, handler):
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
        pmr = handler(self.mapPsl, None, qRngNext, qRngNextNext, None, qStrand,
                      None, tRngNext, tRngNextNext, None, tStrand)
        return qRngNextNext, pmr

    def queryToTargetMap(self, qRngStart, qRngEnd, qStrand=None, handler=PslMapRange.factory):
        """Map a query range to target ranges using a PSL.  If qStrand is not
        specified, query range must be match mapping PSL"""
        if (qStrand is not None) and (qStrand != self.mapPsl.qStrand):
            qRngStart, qRngEnd = _reverseRange(qRngStart, qRngEnd, self.mapPsl.qSize)
        else:
            qStrand = self.mapPsl.qStrand
        tStrand = self.mapPsl.tStrand

        # deal with gap at beginning
        qRngNext = qRngStart
        if qRngNext < self.mapPsl.blocks[0].qStart:
            yield handler(self.mapPsl, None, qRngNext, self.mapPsl.blocks[0].qStart, None, qStrand,
                          None, None, None, self.mapPsl.blocks[0].tStart, tStrand)
            qRngNext = self.mapPsl.blocks[0].qStart

        # process blocks and gaps
        prevBlk = None
        for blk in self.mapPsl.blocks:
            if qRngNext >= qRngEnd:
                break
            if prevBlk is not None:
                qRngNext, pmr = self._q2tProcessGap(prevBlk, blk, qRngNext, qRngEnd, qStrand, tStrand, handler)
                if pmr is not None:
                    yield pmr
            if qRngNext < qRngEnd:
                qRngNext, pmr = self._q2tProcessBlk(blk, qRngNext, qRngEnd, qStrand, tStrand, handler)
                if pmr is not None:
                    yield pmr
            prevBlk = blk

        # deal with gap at end
        lastBlk = self.mapPsl.blocks[self.mapPsl.blockCount - 1]
        if qRngEnd > lastBlk.qEnd:
            yield handler(self.mapPsl, None, max(qRngStart, lastBlk.qEnd), qRngEnd, None, qStrand,
                          lastBlk.tEnd, None, None, None, tStrand)

    def _addRangeToPsl(self, psl, rng, prevRng):
        psl.match += len(rng)
        if prevRng is not None:
            sz = rng.qStart - prevRng.qEnd
            if sz > 0:
                psl.qNumInsert += 1
                psl.qBaseInsert += sz
            sz = rng.tStart - prevRng.tEnd
            if sz > 0:
                psl.tNumInsert += 1
                psl.tBaseInsert += sz
        psl.addBlock(PslBlock(rng.qStart, rng.tStart, len(rng)))

    def _rangesToPsl(self, rangeGen):
        # FIXME: psl building should go a function in Psl
        rngs = [rng for rng in rangeGen if rng.isAligned]
        if len(rngs) == 0:
            return None
        psl = Psl.create()
        psl.qName = self.mapPsl.qName
        psl.qStart = rngs[0].qStart
        psl.qEnd = rngs[-1].qEnd
        psl.qSize = self.mapPsl.qSize
        if rngs[0].qStrand == '-':
            psl.qStart, psl.qEnd = reverseCoords(psl.qStart, psl.qEnd, psl.qSize)
        psl.tName = self.mapPsl.tName
        psl.tStart = rngs[0].tStart
        psl.tEnd = rngs[-1].tEnd
        psl.tSize = self.mapPsl.tSize
        if rngs[0].tStrand == '-':
            psl.tStart, psl.tEnd = reverseCoords(psl.tStart, psl.tEnd, psl.tSize)
        psl.strand = rngs[0].qStrand + ('-' if rngs[0].tStrand == '-' else '')
        prevRng = None
        for rng in rngs:
            self._addRangeToPsl(psl, rng, prevRng)
            prevRng = rng
        return psl

    def targetToQueryMapPsl(self, tRngStart, tRngEnd, tStrand=None):
        """Map a target range to query ranges using a PSL and output a PSL. If tStrand is not
        specified, target range must be match mapping PSL.   Return None if range not mapped."""
        return self._rangesToPsl(self.targetToQueryMap(tRngStart, tRngEnd, tStrand))

    def queryToTargetMapPsl(self, qRngStart, qRngEnd, qStrand=None):
        """Map a query range to query ranges using a PSL and output a PSL. If qStrand is not
        specified, query range must be match mapping PSL.  Return None if range not mapped."""
        return self._rangesToPsl(self.queryToTargetMap(qRngStart, qRngEnd, qStrand))
