# Copyright 2006-2020 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.pslStats import PslStats, PslStatsType

class PslStatsTests(TestCaseBase):
    def testPslAlignStats(self):
        pslStats = PslStats(self.getInputFile("align.pslstats"))
        self.assertEqual(pslStats.type, PslStatsType.ALIGN)
        self.assertEqual(len(pslStats), 32)
        ents = pslStats.idx["NM_000618.2"]
        self.assertEqual(len(ents), 15)
        self.assertEqual(ents[0].qSize, 7260)

    def testPslQueryStats(self):
        pslStats = PslStats(self.getInputFile("query.pslstats"))
        self.assertEqual(pslStats.type, PslStatsType.QUERY)
        self.assertEqual(len(pslStats), 13)
        ent = pslStats.idx["NM_000618.2"]
        self.assertEqual(ent.alnCnt, 15)
        self.assertEqual(ent.qSize, 7260)

    def testPslOverallStats(self):
        pslStats = PslStats(self.getInputFile("overall.pslstats"))
        self.assertEqual(pslStats.type, PslStatsType.OVERALL)
        self.assertEqual(len(pslStats), 1)
        overall = pslStats[0]
        self.assertEqual(overall.queryCnt, 13)
        self.assertEqual(overall.minQSize, 664)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(PslStatsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
