# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.hgdata.rangeFinder import RangeFinder
from collections import namedtuple

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

# for merge test, same sequence
data3 = (
    Data("chr12", 100, 1000, '+', "val1.1"),
    Data("chr12", 100, 1000, '+', "val1.2"),
    Data("chr12", 100, 500, '-', "val1.3"),
    Data("chr12", 150, 10000, '+', "val1.4"),
    Data("chr12", 1000000000, 2000000000, '+', "val1.5"),  # outside of basic range
    Data("chr12", 100000, 2000000000, '-', "val1.6"),  # crossing of basic and extended range
)

def dataMergeFunc(values):
    seqIds = list(set([v.seqId for v in values]))
    if len(seqIds) != 1:
        raise Exception("should only merge one seqId")
    start = min([v.start for v in values])
    end = max([v.end for v in values])
    # values might already be comma separate from previous merge
    strands = []
    vals = []
    for v in values:
        strands.extend(v.strand.split(','))
        vals.extend(v.value.split(','))
    strand = ",".join(sorted(set(strands)))
    value = ",".join(sorted(vals))
    return Data(seqIds[0], start, end, strand, value)

def mkRangeFinder(data, useStrand):
    rf = RangeFinder()
    for row in data:
        if useStrand:
            rf.add(row.seqId, row.start, row.end, row.value, row.strand)
        else:
            rf.add(row.seqId, row.start, row.end, row.value)
    return rf

def doQuery(rf, seqId, start, end, strand):
    "do query and sort results, returning tuple result"
    val = list(rf.overlapping(seqId, start, end, strand))
    val.sort()
    return tuple(val)

def doStrandQuery(rf, query):
    if rf.haveStrand:
        expect = query.expectWithStrand
    else:
        expect = query.expectWithOutStrand
    val = doQuery(rf, query.seqId, query.start, query.end, query.strand)
    assert val == expect

def doNoStrandQuery(rf, query):
    expect = query.expectWithOutStrand
    val = doQuery(rf, query.seqId, query.start, query.end, None)
    assert val == expect

def doQueries(rf, queries, useStrand):
    for query in queries:
        if useStrand:
            doStrandQuery(rf, query)
        else:
            doNoStrandQuery(rf, query)

def testOverlapStrand():
    "stranded queries of have-strand RangeFinder"
    rf = mkRangeFinder(data1, True)
    doQueries(rf, queries1, True)

def testOverlapStrandNoStrand():
    "stranded queries of no-strand RangeFinder"
    rf = mkRangeFinder(data1, False)
    doQueries(rf, queries1, True)

def testOverlapNoStrand():
    "no-stranded queries of no-strand RangeFinder"
    rf = mkRangeFinder(data1, False)
    doQueries(rf, queries1, False)

def testOverlapNoStrandStrand():
    "no-stranded queries of have-strand RangeFinder"
    rf = mkRangeFinder(data1, True)
    doQueries(rf, queries1, False)

def testExactRange():
    "exact range matches"
    rf = mkRangeFinder(data2, True)
    doQueries(rf, queries2, True)
    doQueries(rf, queries2, False)

def testValues():
    "test listing all values"
    rf = mkRangeFinder(data1, True)
    vals = sorted(rf.values())
    assert ['val1.1', 'val1.2', 'val1.3', 'val1.4', 'val1.5', 'val1.6'] == vals

def testRemoveNoStrand():
    "exact range matches"
    rf = mkRangeFinder(data1, False)
    ent = data1[1]  # val1.2
    rf.remove(ent.seqId, ent.start, ent.end, ent.value)
    left = sorted(rf.values())
    expect = ['val1.1', 'val1.3', 'val1.4', 'val1.5', 'val1.6']
    assert left == expect

def testRemoveStrand():
    "exact range matches"
    rf = mkRangeFinder(data1, False)
    ent = data1[1]  # val1.2
    rf.remove(ent.seqId, ent.start, ent.end, ent.value, ent.strand)
    left = sorted(rf.values())
    expect = ['val1.1', 'val1.3', 'val1.4', 'val1.5', 'val1.6']
    assert left == expect

def testGetSeqsStrand():
    rf = mkRangeFinder(data1, True)
    assert rf.getSeqIds() == frozenset([d.seqId for d in data1])

def testGetSeqsNoStrand():
    rf = mkRangeFinder(data1, False)
    assert rf.getSeqIds() == frozenset([d.seqId for d in data1])

def testGetSeqRangeStrand():
    rf = mkRangeFinder(data1, True)
    assert rf.getSeqRange("chr12") == (100, 10000)  # both strands
    assert rf.getSeqRange("chr12", '-') == (100, 500)  # this strand
    assert rf.getSeqRange("chr55") == (None, None)
    assert rf.getSeqRange("chr55", '-') == (None, None)

def testGetSeqRangeNoStrand():
    rf = mkRangeFinder(data1, False)
    assert rf.getSeqRange("chr12") == (100, 10000)  # both strands
    assert rf.getSeqRange("chr12", '-') == (100, 10000)  # also for both
    assert rf.getSeqRange("chr55") == (None, None)
    assert rf.getSeqRange("chr55", '-') == (None, None)

def mkRangeFinderMerge(data, useStrand):
    rf = RangeFinder(mergeFunc=dataMergeFunc)
    for row in data:
        if useStrand:
            rf.addMerge(row.seqId, row.start, row.end, row, row.strand)
        else:
            rf.addMerge(row.seqId, row.start, row.end, row)
    return rf

def testMergerStrand1():
    rf = mkRangeFinderMerge(data1, True)
    values = sorted(rf.values())
    assert values == [
        Data(seqId='chr12', start=100, end=500, strand='-', value='val1.3'),
        Data(seqId='chr12', start=100, end=10000, strand='+', value='val1.2,val1.4'),
        Data(seqId='chr22', start=100, end=1000, strand='+', value='val1.1'),
        Data(seqId='chr32', start=100000, end=2000000000, strand='-', value='val1.6'),
        Data(seqId='chr32', start=1000000000, end=2000000000, strand='+', value='val1.5')
    ]

def testMergerNoStrand1():
    rf = mkRangeFinderMerge(data1, False)
    values = sorted(rf.values())
    assert values == [
        Data(seqId='chr12', start=100, end=10000, strand='+,-', value='val1.2,val1.3,val1.4'),
        Data(seqId='chr22', start=100, end=1000, strand='+', value='val1.1'),
        Data(seqId='chr32', start=100000, end=2000000000, strand='+,-', value='val1.5,val1.6')
    ]

def testMergerStrand3():
    rf = mkRangeFinderMerge(data3, True)
    values = sorted(rf.values())
    assert values == [
        Data(seqId='chr12', start=100, end=500, strand='-', value='val1.3'),
        Data(seqId='chr12', start=100, end=10000, strand='+', value='val1.1,val1.2,val1.4'),
        Data(seqId='chr12', start=100000, end=2000000000, strand='-', value='val1.6'),
        Data(seqId='chr12', start=1000000000, end=2000000000, strand='+', value='val1.5')
    ]

def testMergerNoStrand3():
    rf = mkRangeFinderMerge(data3, False)
    values = sorted(rf.values())
    assert values == [
        Data(seqId='chr12', start=100, end=10000, strand='+,-', value='val1.1,val1.2,val1.3,val1.4'),
        Data(seqId='chr12', start=100000, end=2000000000, strand='+,-', value='val1.5,val1.6')
    ]
