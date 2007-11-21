import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.align.PairAlign import loadPslFile

class PairAlignPsl(TestCaseBase):
    def testLoad(self):
        pairAlns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                               self.getInputFile("hsRefSeq.cds"))
        fh = open(self.getOutputFile(".out"), "w")
        for pa in pairAlns:
            pa.dump(fh)
        fh.close()
        self.diffExpected(".out")

    def testRevCmpl(self):
        pairAlns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                               self.getInputFile("hsRefSeq.cds"))
        rfh = open(self.getOutputFile(".rout"), "w")
        rrfh = open(self.getOutputFile(".rrout"), "w")
        for pa in pairAlns:
            rpa = pa.revCmpl()
            rpa.dump(rfh)
            rrpa = rpa.revCmpl()
            rrpa.dump(rrfh)
        rfh.close()
        rrfh.close()
        self.diffExpected(".rout")
        self.diffExpected(".rrout")

    def testLoadUnaln(self):
        pairAlns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                               self.getInputFile("hsRefSeq.cds"),
                               inclUnaln=True)
        fh = open(self.getOutputFile(".out"), "w")
        for pa in pairAlns:
            pa.dump(fh)
        fh.close()
        self.diffExpected(".out")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PairAlignPsl))
    return suite

if __name__ == '__main__':
    unittest.main()
