# Copyright 2015-2016 Mark Diekhans
import unittest
import sys
import shutil
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import fileOps, procOps


class FileOpsTests(TestCaseBase):
    def testOpengzReadPlain(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        with fileOps.opengz(inf) as inFh, open(outf, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        self.diffFiles(inf, outf)

    def testOpengzWritePlain(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        with open(inf) as inFh, fileOps.opengz(outf, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        self.diffFiles(inf, outf)

    def testOpengzReadGz(self):
        inf = self.getInputFile("simple1.txt")
        infGz = self.getOutputFile(".out.gz")
        procOps.runProc(("gzip", "-c", inf), stdout=infGz)
        outf = self.getOutputFile(".out")
        with fileOps.opengz(infGz) as inFh, open(outf, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        self.diffFiles(inf, outf)

    def testOpengzWriteGz(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        outfGz = self.getOutputFile(".out.gz")
        with open(inf) as inFh, fileOps.opengz(outfGz, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        procOps.runProc(("gunzip", "-c", outfGz), stdout=outf)
        self.diffFiles(inf, outf)

    def testOpengzReadBz2(self):
        inf = self.getInputFile("simple1.txt")
        infBz2 = self.getOutputFile(".out.bz2")
        procOps.runProc(("bzip2", "-c", inf), stdout=infBz2)
        outf = self.getOutputFile(".out")
        with fileOps.opengz(infBz2) as inFh, open(outf, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        self.diffFiles(inf, outf)

    def testOpengzWriteBz2(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        outfBz2 = self.getOutputFile(".out.bz2")
        with open(inf) as inFh, fileOps.opengz(outfBz2, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        procOps.runProc(("bunzip2", "-c", outfBz2), stdout=outf)
        self.diffFiles(inf, outf)

    def testAtomicInstall(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        outfTmp = fileOps.atomicTmpFile(outf)
        with open(inf) as inFh, open(outfTmp, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        fileOps.atomicInstall(outfTmp, outf)
        self.diffFiles(inf, outf)


# FIXME: many more tests needed


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(FileOpsTests))
    return ts

if __name__ == '__main__':
    unittest.main()
