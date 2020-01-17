# Copyright 2015-2016 Mark Diekhans
import unittest
import os
import sys
import shutil
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
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
        shutil.copyfile(inf, outfTmp)
        fileOps.atomicInstall(outfTmp, outf)
        self.diffFiles(inf, outf)

    def testAtomicInstallDev(self):
        devn = '/dev/null'
        tmp = fileOps.atomicTmpFile(devn)
        self.assertEqual(tmp, devn)
        fileOps.atomicInstall(tmp, devn)

    def testAtomicContextOk(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        with fileOps.AtomicFileCreate(outf) as outfTmp:
            shutil.copyfile(inf, outfTmp)
        self.diffFiles(inf, outf)

    def testAtomicContextError(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        try:
            with fileOps.AtomicFileCreate(outf) as outfTmp:
                shutil.copyfile(inf, outfTmp)
                raise Exception("stop!")
        except Exception as ex:
            self.assertEqual(str(ex), "stop!")
        self.assertFalse(os.path.exists(outf))

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

    def testMd5Sum(self):
        md5 = fileOps.md5sum(self.getInputFile("simple1.txt"))
        self.assertEqual('b256e7fa23f105539085c7c895557c41', md5)

    def testMd5Sums(self):
        expected = [("simple1.txt", "b256e7fa23f105539085c7c895557c41"),
                    ("comments1.txt", "4179a04267de41833d87e182b22999ca"),
                    ("funcArgs.config.py", "6df2aec2f839ff35ea26ca8440baee2d")]
        got = fileOps.md5sums([self.getInputFile(f[0]) for f in expected])
        self.assertEqual(len(expected), len(got))
        for e, g in zip(expected, got):
            self.assertEqual(e[0], os.path.basename(g[0]))
            self.assertEqual(e[1], g[1])


# FIXME: many more tests needed


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(FileOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
