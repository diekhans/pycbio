# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.geneCheck import GeneCheckTbl


class ReadTests(TestCaseBase):
    def _dumpCheck(self, fh, checks, g):
        g.dump(fh)
        if checks.haveDetails():
            details = checks.getDetails(g)
            if details is not None:
                for d in details:
                    fh.write('\t')
                    d.dump(fh)

    def _checkDmp(self, checks):
        with open(self.getOutputFile(".dmp"), 'w') as fh:
            for g in checks:
                self._dumpCheck(fh, checks, g)
        self.diffExpected(".dmp")

    def testCheck(self):
        checks = GeneCheckTbl(self.getInputFile("geneCheck.tsv"))
        self.assertEqual(len(checks), 162)
        self._checkDmp(checks)

    def testCheckDetails(self):
        checks = GeneCheckTbl(self.getInputFile("geneCheck.tsv"),
                              self.getInputFile("geneCheckDetails.tsv"))
        self.assertEqual(len(checks), 162)
        self._checkDmp(checks)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ReadTests))
    return ts


if __name__ == '__main__':
    unittest.main()
