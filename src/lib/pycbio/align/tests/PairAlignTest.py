import unittest, sys, copy
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.align.PairAlign import loadPslFile

class PairAlignPsl(TestCaseBase):
    def __dumpNDiff(self, alns, suffix):
        fh = open(self.getOutputFile(suffix), "w")
        for pa in alns:
            pa.dump(fh)
        fh.close()
        self.diffExpected(suffix)
        
    def testLoad(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                           self.getInputFile("hsRefSeq.cds"))
        self.__dumpNDiff(alns, ".out")

    def testRevCmpl(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                               self.getInputFile("hsRefSeq.cds"))
        ralns = []
        rralns = []
        for pa in alns:
            rpa = pa.revCmpl()
            ralns.append(rpa)
            rralns.append(rpa.revCmpl())
        self.__dumpNDiff(ralns, ".rout")
        self.__dumpNDiff(rralns, ".rrout")

    def testLoadUnaln(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                           self.getInputFile("hsRefSeq.cds"),
                           inclUnaln=True)
        self.__dumpNDiff(alns, ".out")

    def testProjectCds(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                           self.getInputFile("hsRefSeq.cds"),
                           inclUnaln=True)
        qalns = []
        for pa in alns:
            pa.projectCdsToTarget()
            # project back
            qpa = copy.deepcopy(pa)
            qpa.qSubSeqs.clearCds()
            qpa.projectCdsToQuery()
            qalns.append(qpa)
        self.__dumpNDiff(alns, ".tout")
        self.__dumpNDiff(alns, ".qout")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PairAlignPsl))
    return suite

if __name__ == '__main__':
    unittest.main()
