# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys.fileOps import prRowv
from pycbio.align.pairAlign import loadPslFile
from pycbio import PycbioException


class WithSrcCds(object):
    "container for map CDS results"
    def __init__(self, srcAln, destAln):
        self.srcAln = srcAln
        self.destAln = destAln

    def dump(self, fh):
        prRowv(fh, "srcQCds: ", self.srcAln.qSeq)
        prRowv(fh, "srcTCds: ", self.srcAln.tSeq)
        self.destAln.dump(fh)


class PairAlignPsl(TestCaseBase):
    def _dumpNDiff(self, alns, suffix):
        with open(self.getOutputFile(suffix), "w") as fh:
            for pa in alns:
                pa.dump(fh)
        self.diffExpected(suffix)

    def testLoad(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                           self.getInputFile("hsRefSeq.cds"))
        self._dumpNDiff(alns, ".out")

    def testRevCmpl(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                           self.getInputFile("hsRefSeq.cds"))
        ralns = []
        rralns = []
        for pa in alns:
            rpa = pa.revCmpl()
            ralns.append(rpa)
            rralns.append(rpa.revCmpl())
        self._dumpNDiff(ralns, ".rout")
        self._dumpNDiff(rralns, ".rrout")

    def testLoadUnaln(self):
        alns = loadPslFile(self.getInputFile("hsRefSeq.psl"),
                           self.getInputFile("hsRefSeq.cds"),
                           inclUnaln=True)
        self._dumpNDiff(alns, ".out")

    def doTestProjectCds(self, contained):
        alns = loadPslFile(self.getInputFile("refseqWeird.psl"),
                           self.getInputFile("refseqWeird.cds"),
                           inclUnaln=True)
        qalns = []
        for pa in alns:
            pa.projectCdsToTarget(contained=contained)
            # project back
            qpa = pa.copy()
            qpa.qSubSeqs.clearCds()
            qpa.projectCdsToQuery(contained=contained)
            qalns.append(qpa)
        self._dumpNDiff(alns, ".tout")
        self._dumpNDiff(qalns, ".qout")

    def testProjectCds(self):
        self.doTestProjectCds(False)

    def testProjectCdsContained(self):
        self.doTestProjectCds(True)

    def doTestMapCds(self, contained):
        destAlns = loadPslFile(self.getInputFile("clonesWeird.psl"),
                               inclUnaln=True)
        srcAlns = loadPslFile(self.getInputFile("refseqWeird.psl"),
                              self.getInputFile("refseqWeird.cds"),
                              inclUnaln=True,
                              projectCds=True)
        mappedAlns = []
        for destAln in destAlns:
            for srcAln in srcAlns:
                if srcAln.qSeq.cds is None:
                    raise PycbioException("no qCDS: " + srcAln.qSeq.id + " <=> " + srcAln.tSeq.id)
                if srcAln.tSeq.cds is None:
                    raise PycbioException("no tCDS: " + srcAln.qSeq.id + " <=> " + srcAln.tSeq.id)
                if srcAln.targetOverlap(destAln):
                    ma = destAln.copy()
                    ma.mapCds(srcAln, srcAln.tSeq, ma.tSeq, contained=contained)
                    mappedAlns.append(WithSrcCds(srcAln, ma))
        self._dumpNDiff(mappedAlns, ".out")

    def testMapCds(self):
        self.doTestMapCds(contained=False)

    def testMapCdsContained(self):
        self.doTestMapCds(contained=True)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(PairAlignPsl))
    return ts


if __name__ == '__main__':
    unittest.main()
