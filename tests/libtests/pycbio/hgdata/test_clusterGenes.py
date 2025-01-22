# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.clusterGenes import ClusterGenes


class ReadTests(TestCaseBase):
    def testLoad(self):
        clusters = ClusterGenes(self.getInputFile("models.loci"))

        clCnt = 0
        geneCnt = 0
        for cl in clusters:
            clCnt += 1
            for g in cl:
                geneCnt += 1
        self.assertEqual(clCnt, 16)
        self.assertEqual(geneCnt, 49)

        # try getting gene, and go back to it's cluster
        self.assertEqual(len(clusters.genes["NR_046018.2"]), 1)
        g = clusters.genes["ENST00000335137.4"][0]
        cl = g.clusterObj
        self.assertEqual(len(cl), 3)
        self.assertEqual(frozenset([g.gene for g in cl]),
                         frozenset(["ENST00000335137.4", "NM_001005484.1", "ENST00000641515.2"]))

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ReadTests))
    return ts


if __name__ == '__main__':
    unittest.main()
