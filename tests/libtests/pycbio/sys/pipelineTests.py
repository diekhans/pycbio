# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
import StringIO
if __name__ == '__main__':
    sys.path.extend(["../../..", "../../../.."])
from pycbio.sys.pipeline import Pipeline, ProcException, DataReader
from pycbio.sys import procOps
from pycbio.hgdata.genePred import GenePredFhReader
from pycbio.sys.testCaseBase import TestCaseBase

# FIXME from: ccds2/modules/gencode/src/progs/gencodeMakeTracks/gencodeGtfToGenePred
# this doesn't work, nothing is returned by the readers,
# used to fix Pipeline at some time


class ChrMLifterBROKEN(object):
    "Do lifting to of chrM"
    def __init__(self, liftFile):
        self.mappedRd = DataReader()
        self.droppedRd = DataReader()
        self.pipeline = Pipeline(["liftOver", "-genePred", "stdin", liftFile, self.mappedRd, self.droppedRd], "w")

    def write(self, gp):
        gp.name = "NC_012920"
        gp.write(self.pipeline)

    def __checkForDropped(self):
        "check if anything written to the dropped file"
        dropped = [gp for gp in GenePredFhReader(StringIO(self.droppedRd.get()))]
        if len(dropped) > 0:
            raise Exception("chrM liftOver dropped " + str(len(dropped)) + " records")

    def finishLifting(self, gpOutFh):
        self.pipeline.wait()
        for gp in GenePredFhReader(StringIO(self.mappedRd.get())):
            gp.write(gpOutFh)
        self.__checkForDropped()


class PipelineTests(TestCaseBase):
    def cpFileToPl(self, inName, pl):
        inf = self.getInputFile(inName)
        fh = open(inf)
        for line in fh:
            pl.write(line)
        fh.close()

    def testWrite(self):
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        outfGz = self.getOutputFile(".out.gz")

        pl = Pipeline(("gzip", "-1"), "w", otherEnd=outfGz)
        self.cpFileToPl("simple1.txt", pl)
        pl.wait()

        procOps.runProc(("zcat", outfGz), stdout=outf)
        self.diffFiles(inf, outf)

    def BROKEN_testWriteFile(self):
        outf = self.getOutputFile(".out")
        outfGz = self.getOutputFile(".out.gz")

        with open(outfGz, "w") as outfGzFh:
            pl = Pipeline(("gzip", "-1"), "w", otherEnd=outfGzFh)
            self.cpFileToPl("simple1.txt", pl)
            pl.wait()

        procOps.runProc(("zcat", outfGz), stdout=outf)
        self.diffExpected(".out")

    def testWriteMult(self):
        outf = self.getOutputFile(".wc")

        # grr, BSD wc adds an extract space, so just convert to tabs
        pl = Pipeline((("gzip", "-1"),
                       ("gzip", "-dc"),
                       ("wc",),
                       ("sed", "-e", "s/  */\t/g")),
                      "w", otherEnd=outf)
        self.cpFileToPl("simple1.txt", pl)
        pl.wait()

        self.diffExpected(".wc")

    def cpPlToFile(self, pl, outExt):
        outf = self.getOutputFile(outExt)
        fh = open(outf, "w")
        for line in pl:
            fh.write(line)
        fh.close()
        return outf

    def testRead(self):
        inf = self.getInputFile("simple1.txt")
        infGz = self.getOutputFile(".txt.gz")
        procOps.runProc(("gzip", "-c", inf), stdout=infGz)

        pl = Pipeline(("gzip", "-dc"), "r", otherEnd=infGz)
        outf = self.cpPlToFile(pl, ".out")
        pl.wait()

        self.diffFiles(inf, outf)

    def testReadMult(self):
        inf = self.getInputFile("simple1.txt")

        pl = Pipeline((("gzip", "-1c"),
                       ("gzip", "-dc"),
                       ("wc",),
                       ("sed", "-e", "s/  */\t/g")),
                      "r", otherEnd=inf)
        self.cpPlToFile(pl, ".wc")
        pl.wait()

        self.diffExpected(".wc")

    def XXtestPassRead(self):
        "using FIFO to pass pipe to another process for reading"
        # FIXME: should this be supported somehow
        inf = self.getInputFile("simple1.txt")
        infGz = self.getOutputFile(".txt.gz")
        cpOut = self.getOutputFile(".out")
        procOps.runProc(("gzip", "-c", inf), stdout=infGz)

        pl = Pipeline(("gzip", "-dc"), "r", otherEnd=infGz)
        procOps.runProc(["cat"], stdin=pl.pipePath, stdout=cpOut)
        pl.wait()

        self.diffFiles(inf, cpOut)

    def XXtestPassWrite(self):
        "using FIFO to pass pipe to another process for writing"
        # FIXME: should this be supported somehow
        inf = self.getInputFile("simple1.txt")
        outf = self.getOutputFile(".out")
        pipePath = self.getOutputFile(".fifo")

        pl = Pipeline(("sort", "-r"), "w", otherEnd=outf, pipePath=pipePath)
        procOps.runProc(["cat"], stdin=inf, stdout=pl.pipePath)
        pl.wait()

        self.diffExpected(".out")

    def testExitCode(self):
        pl = Pipeline(("false",))
        with self.assertRaises(ProcException):
            pl.wait()
        for p in pl.procs:
            self.assertTrue(p.returncode == 1)

    def testSigPipe(self):
        "test not reading all of pipe output"
        pl = Pipeline([("yes",), ("true",)], "r")
        pl.wait()


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(PipelineTests))
    return ts

if __name__ == '__main__':
    unittest.main()
