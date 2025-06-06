# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.stats.venn import Venn
from pycbio.sys.testCaseBase import TestCaseBase


class VennTests(TestCaseBase):
    def _checkVenn(self, venn):
        with open(self.getOutputFile(".vinfo"), "w") as viFh:
            venn.writeSets(viFh)
        with open(self.getOutputFile(".vcnts"), "w") as viFh:
            venn.writeCounts(viFh)
        with open(self.getOutputFile(".vmat"), "w") as viFh:
            venn.writeCountMatrix(viFh)
        self.diffExpected(".vinfo")
        self.diffExpected(".vcnts")
        self.diffExpected(".vmat")

    def testVenn1(self):
        venn = Venn()
        venn.addItems("A", (1, 2, 3))
        venn.addItems("B", (3, 4, 5))
        venn.addItems("C", (3, 5, 6))
        self._checkVenn(venn)

    def testVenn2(self):
        venn = Venn(isInclusive=True)
        venn.addItems("A", (1, 2, 3))
        venn.addItems("B", (3, 4, 5))
        venn.addItems("C", (3, 5, 6))
        self._checkVenn(venn)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(VennTests))
    return ts


if __name__ == '__main__':
    unittest.main()
