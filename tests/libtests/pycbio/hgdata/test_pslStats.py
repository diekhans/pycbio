# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.pslStats import PslStats, PslStatsType

def testPslAlignStats(request):
    pslStats = PslStats(ts.get_test_input_file(request, "align.pslstats"))
    assert pslStats.type == PslStatsType.ALIGN
    assert len(pslStats) == 32
    ents = pslStats.idx["NM_000618.2"]
    assert len(ents) == 15
    assert ents[0].qSize == 7260

def testPslQueryStats(request):
    pslStats = PslStats(ts.get_test_input_file(request, "query.pslstats"))
    assert pslStats.type == PslStatsType.QUERY
    assert len(pslStats) == 13
    ent = pslStats.idx["NM_000618.2"]
    assert ent.alnCnt == 15
    assert ent.qSize == 7260

def testPslOverallStats(request):
    pslStats = PslStats(ts.get_test_input_file(request, "overall.pslstats"))
    assert pslStats.type == PslStatsType.OVERALL
    assert len(pslStats) == 1
    overall = pslStats[0]
    assert overall.queryCnt == 13
    assert overall.minQSize == 664
