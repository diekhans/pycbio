# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.rangeFinder import RangeFinder
from collections import namedtuple

debug = True

# test data and query types
Data = namedtuple("Data", ("seqId", "start", "end", "strand", "value"))
Query = namedtuple("Query", ("seqId", "start", "end", "strand", "expectWithStrand", "expectWithOutStrand"))

data1 = (
    Data("chr22", 100, 1000, '+', "val1.1"),
    Data("chr12", 100, 1000, '+', "val1.2"),
    Data("chr12", 100, 500, '-', "val1.3"),
    Data("chr12", 150, 10000, '+', "val1.4"),
    Data("chr32", 1000000000, 2000000000, '+', "val1.5"),  # outside of basic range
    Data("chr32", 100000, 2000000000, '-', "val1.6"),  # crossing of basic and extended range
)
# (seqId start end strand expectWithStrand expectWithoutStrand)
queries1 = (
    Query("chr20", 100, 1000, '+', (), ()),
    Query("chr22", 100, 1000, '+', ("val1.1",), ("val1.1",)),
    Query("chr22", 100, 1000, '-', (), ("val1.1",)),
    Query("chr22", 110, 111, '+', ("val1.1",), ("val1.1",)),
    Query("chr22", 110, 111, '-', (), ("val1.1",)),
    Query("chr12", 1, 150, '-', ("val1.3",), ("val1.2", "val1.3")),
    Query("chr12", 10000, 1500000, '+', (), ()),
    Query("chr12", 1, 151, '-', ("val1.3",), ("val1.2", "val1.3", "val1.4")),
    Query("chr12", 1, 151, '+', ("val1.2", "val1.4"), ("val1.2", "val1.3", "val1.4")),
    Query("chr32", 10, 100001, '+', (), ("val1.6",)),
    Query("chr32", 10, 1000000001, '+', ("val1.5",), ("val1.5", "val1.6",)),
    Query("chr32", 1900000001, 2000000002, '+', ("val1.5",), ("val1.5", "val1.6",)),
)

# potential regression with exact range matches
data2 = (
    Data("chr1", 100316598, 100387207, '+', "NM_000643.2"),
    Data("chr1", 100316598, 100387207, '+', "NM_000644.2"),
)
queries2 = (
    Query("chr1", 100316598, 100387207, '+', ("NM_000643.2", "NM_000644.2"), ("NM_000643.2", "NM_000644.2")),
)


class RangeTests(TestCaseBase):
    def mkRangeFinder(self, data, useStrand):
        rf = RangeFinder()
        for row in data:
            if useStrand:
                rf.add(row.seqId, row.start, row.end, row.value, row.strand)
            else:
                rf.add(row.seqId, row.start, row.end, row.value)
        return rf

    def failTrace(self, desc, query, expect, got):
        msg = "{} query failed: {}:{}-{} {}: expect: {}\n\tgot: {}\n".format(desc, query.seqId, query.start, query.end, query.strand, str(expect), str(got))
        sys.stderr.write(msg)
        sys.stderr.flush()

    def doQuery(self, rf, seqId, start, end, strand):
        "do query and sort results, returning tuple result"
        val = list(rf.overlapping(seqId, start, end, strand))
        val.sort()
        return tuple(val)

    def doStrandQuery(self, rf, query):
        if rf.haveStrand:
            expect = query.expectWithStrand
        else:
            expect = query.expectWithOutStrand
        val = self.doQuery(rf, query.seqId, query.start, query.end, query.strand)
        if debug and (val != expect):
            self.failTrace("strand of haveStrand={}".format(rf.haveStrand), query, expect, val)
        self.assertEqual(val, expect)

    def doNoStrandQuery(self, rf, query):
        expect = query.expectWithOutStrand
        val = self.doQuery(rf, query.seqId, query.start, query.end, None)
        if debug and (val != expect):
            self.failTrace("no-strand of haveStrand={}".format(rf.haveStrand), query, expect, val)
        self.assertEqual(val, expect)

    def doQueries(self, rf, queries, useStrand):
        for query in queries:
            if useStrand:
                self.doStrandQuery(rf, query)
            else:
                self.doNoStrandQuery(rf, query)

    def testOverlapStrand(self):
        "stranded queries of have-strand RangeFinder"
        rf = self.mkRangeFinder(data1, True)
        self.doQueries(rf, queries1, True)

    def testOverlapStrandNoStrand(self):
        "stranded queries of no-strand RangeFinder"
        rf = self.mkRangeFinder(data1, False)
        self.doQueries(rf, queries1, True)

    def testOverlapNoStrand(self):
        "no-stranded queries of no-strand RangeFinder"
        rf = self.mkRangeFinder(data1, False)
        self.doQueries(rf, queries1, False)

    def testOverlapNoStrandStrand(self):
        "no-stranded queries of have-strand RangeFinder"
        rf = self.mkRangeFinder(data1, True)
        self.doQueries(rf, queries1, False)

    def testExactRange(self):
        "exact range matches"
        rf = self.mkRangeFinder(data2, True)
        self.doQueries(rf, queries2, True)
        self.doQueries(rf, queries2, False)

    def testValues(self):
        "test listing all values"
        rf = self.mkRangeFinder(data1, True)
        vals = sorted(rf.values())
        self.assertEqual(['val1.1', 'val1.2', 'val1.3', 'val1.4', 'val1.5', 'val1.6'],
                         vals)

    def testRemoveNoStrand(self):
        "exact range matches"
        rf = self.mkRangeFinder(data1, False)
        ent = data1[1]  # val1.2
        rf.remove(ent.seqId, ent.start, ent.end, ent.value)
        left = sorted(rf.values())
        expect = ['val1.1', 'val1.3', 'val1.4', 'val1.5', 'val1.6']
        self.assertEqual(left, expect)

    def testRemoveStrand(self):
        "exact range matches"
        rf = self.mkRangeFinder(data1, False)
        ent = data1[1]  # val1.2
        rf.remove(ent.seqId, ent.start, ent.end, ent.value, ent.strand)
        left = sorted(rf.values())
        expect = ['val1.1', 'val1.3', 'val1.4', 'val1.5', 'val1.6']
        self.assertEqual(left, expect)

    def testGetSeqsStrand(self):
        rf = self.mkRangeFinder(data1, True)
        self.assertEqual(rf.getSeqIds(), frozenset([d.seqId for d in data1]))

    def testGetSeqsNoStrand(self):
        rf = self.mkRangeFinder(data1, False)
        self.assertEqual(rf.getSeqIds(), frozenset([d.seqId for d in data1]))

    def testGetSeqRangeStrand(self):
        rf = self.mkRangeFinder(data1, True)
        self.assertEqual(rf.getSeqRange("chr12"), (100, 10000))  # both strands
        self.assertEqual(rf.getSeqRange("chr12", '-'), (100, 500))  # this strand
        self.assertEqual(rf.getSeqRange("chr55"), (None, None))
        self.assertEqual(rf.getSeqRange("chr55", '-'), (None, None))

    def testGetSeqRangeNoStrand(self):
        rf = self.mkRangeFinder(data1, False)
        self.assertEqual(rf.getSeqRange("chr12"), (100, 10000))  # both strands
        self.assertEqual(rf.getSeqRange("chr12", '-'), (100, 10000))  # also for both
        self.assertEqual(rf.getSeqRange("chr55"), (None, None))
        self.assertEqual(rf.getSeqRange("chr55", '-'), (None, None))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(RangeTests))
    return ts


if __name__ == '__main__':
    unittest.main()
