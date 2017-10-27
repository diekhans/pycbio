# Copyright 2015-2016 Mark Diekhans
import unittest
import sys
import shutil
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import fileOps
import pipettor


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
        pipettor.run(("gzip", "-c", inf), stdout=infGz)
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
        pipettor.run(("gunzip", "-c", outfGz), stdout=outf)
        self.diffFiles(inf, outf)

    def testOpengzReadBz2(self):
        inf = self.getInputFile("simple1.txt")
        infBz2 = self.getOutputFile(".out.bz2")
        pipettor.run(("bzip2", "-c", inf), stdout=infBz2)
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
        pipettor.run(("bunzip2", "-c", outfBz2), stdout=outf)
        self.diffFiles(inf, outf)

    def testAtomicInstall(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        outfTmp = fileOps.atomicTmpFile(outf)
        with open(inf) as inFh, open(outfTmp, "w") as outFh:
            shutil.copyfileobj(inFh, outFh)
        fileOps.atomicInstall(outfTmp, outf)
        self.diffFiles(inf, outf)

    simple1Lines = ['one', 'two', 'three', 'four', 'five', 'six']

    def testReadFileLines(self):
        lines = fileOps.readFileLines(self.getInputFile("simple1.txt"))
        self.assertEqual(self.simple1Lines, lines)

    def testReadNonCommentLines(self):
        lines = fileOps.readNonCommentLines(self.getInputFile("comments1.txt"))
        self.assertEqual(self.simple1Lines, lines)

    def testIterLineName(self):
        lines = [l for l in fileOps.iterLines(self.getInputFile("simple1.txt"))]
        self.assertEqual(self.simple1Lines, lines)

    def testIterLineFh(self):
        with open(self.getInputFile("simple1.txt")) as fh:
            lines = [l for l in fileOps.iterLines(fh)]
        self.assertEqual(self.simple1Lines, lines)


# FIXME: many more tests needed


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(FileOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
