# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.geneCheck import GeneCheckTbl


class ReadTests(TestCaseBase):
    def __checkDmp(self, checks):
        dmp = self.getOutputFile(".dmp")
        dmpfh = open(dmp, "w")
        for g in checks:
            g.dump(dmpfh)
        dmpfh.close()
        self.diffExpected(".dmp")

    def testRdbUniq(self):
        checks = GeneCheckTbl(self.getInputFile("geneCheck.rdb"), idIsUniq=True, isRdb=True)
        self.assertEqual(len(checks), 53)
        self.__checkDmp(checks)

    def testTsvUniq(self):
        checks = GeneCheckTbl(self.getInputFile("geneCheck.tsv"), idIsUniq=True, isRdb=False)
        self.assertEqual(len(checks), 53)
        self.__checkDmp(checks)

    def testRdbMulti(self):
        checks = GeneCheckTbl(self.getInputFile("geneCheckMulti.rdb"), isRdb=True)
        self.assertEqual(len(checks), 8)
        self.__checkDmp(checks)

    def testTsvMulti(self):
        checks = GeneCheckTbl(self.getInputFile("geneCheckMulti.tsv"), isRdb=False)
        self.assertEqual(len(checks), 8)
        self.__checkDmp(checks)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ReadTests))
    return ts

if __name__ == '__main__':
    unittest.main()
