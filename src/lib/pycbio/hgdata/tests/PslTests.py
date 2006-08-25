import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.hgdata.Psl import Psl
from pycbio.hgdata.Psl import PslTbl

class ReadTests(TestCaseBase):
    def testLoad(self):
        pslTbl = PslTbl(self.getInputFile("pslTest.psl"))
        self.failUnlessEqual(len(pslTbl), 14)
        r = pslTbl[1]
        self.failUnlessEqual(r.blockCount, 13)
        self.failUnlessEqual(len(r.tStarts), 13)
        self.failUnlessEqual(r.qName, "NM_198943.1")

    def countQNameHits(self, pslTbl, qName):
        cnt = 0
        for p in pslTbl.getByQName(qName):
            self.failUnlessEqual(p.qName, qName)
            cnt += 1
        return cnt

    def testQNameIdx(self):
        pslTbl = PslTbl(self.getInputFile("pslTest.psl"), qNameIdx=True)
        self.failIf(pslTbl.haveQName("fred"))
        self.failUnless(pslTbl.haveQName("NM_001327.1"))
        self.failUnlessEqual(self.countQNameHits(pslTbl, "NM_198943.1"), 1)
        self.failUnlessEqual(self.countQNameHits(pslTbl, "fred"), 0)
        self.failUnlessEqual(self.countQNameHits(pslTbl, "NM_000014.3"), 2)
        self.failUnlessEqual(self.countQNameHits(pslTbl, "NM_001327.1"), 4)
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ReadTests))
    return suite

if __name__ == '__main__':
    unittest.main()
