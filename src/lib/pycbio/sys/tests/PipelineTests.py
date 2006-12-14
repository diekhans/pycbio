import unittest, sys, string
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.Pipeline import Pipeline
from pycbio.sys import procOps
from pycbio.sys.TestCaseBase import TestCaseBase

class PipelineTests(TestCaseBase):
    def cpFileToPl(self, inName, pl):
        inFile = self.getInputFile(inName)
        fh = open(inFile)
        for line in fh:
            pl.fh.write(line)
        fh.close()
    
    def testWrite(self):
        outFile = self.getOutputFile(".out")
        outFileGz = self.getOutputFile(".out.gz")

        pl = Pipeline(("gzip", "-1"), "w", otherEnd=outFileGz)
        self.cpFileToPl("simple1.txt", pl)
        pl.wait()

        procOps.runProc(("zcat", outFileGz), stdout=outFile)
        self.diffExpected(".out")

    def testWriteMult(self):
        outFile = self.getOutputFile(".wc")

        # grr, BSD wc adds an extract space, so just convert to tabs
        pl = Pipeline((("gzip", "-1"),
                       ("gzip", "-dc"),
                       ("wc",),
                       ("sed", "-e", "s/ */\t/g")),
                      "w", otherEnd=outFile)
        self.cpFileToPl("simple1.txt", pl)
        pl.wait()

        self.diffExpected(".wc")

    def cpPlToFile(self, pl, outExt):
        outFile = self.getOutputFile(outExt)
        fh = open(outFile, "w")
        for line in pl.fh:
            fh.write(line)
        fh.close()
    
    def testRead(self):
        inFile = self.getInputFile("simple1.txt")
        inFileGz = self.getOutputFile(".txt.gz")
        procOps.runProc(("gzip", "-c", inFile), stdout=inFileGz)

        pl = Pipeline(("gzip", "-dc"), "r", otherEnd=inFileGz)
        self.cpPlToFile(pl, ".out")
        pl.wait()

        self.diffExpected(".out")

    def testReadMult(self):
        inFile = self.getInputFile("simple1.txt")
        inFileGz = self.getOutputFile(".txt.gz")
        procOps.runProc(("gzip", "-c", inFile), stdout=inFileGz)

        pl = Pipeline((("gzip","-1"),
                       ("gzip", "-dc"),
                       ("wc",),
                       ("sed", "-e", "s/ */\t/g")),
                      "r", otherEnd=inFileGz)
        self.cpPlToFile(pl, ".wc")
        pl.wait()

        self.diffExpected(".wc")

    def testPassRead(self):
        "using /proc fs to pass pipe to another process for reading"
        inFile = self.getInputFile("simple1.txt")
        inFileGz = self.getOutputFile(".txt.gz")
        cpOut = self.getOutputFile(".out")
        procOps.runProc(("gzip", "-c", inFile), stdout=inFileGz)

        pl = Pipeline(("gzip", "-dc"), "r", otherEnd=inFileGz)
        procOps.runProc(["cat"],  stdin=pl.pipepath(), stdout=cpOut)
        pl.wait()

        self.diffExpected(".out")

    def testPassWrite(self):
        "using /proc fs to pass pipe to another process for writing"
        inFile = self.getInputFile("simple1.txt")
        outFile = self.getOutputFile(".out")

        pl = Pipeline(("sort", "-r"), "w", otherEnd=outFile)
        procOps.runProc(["cat"],  stdin=inFile, stdout=pl.pipepath())
        pl.wait()

        self.diffExpected(".out")

    def testExitCode(self):
        p = Pipeline(("false",))
        self.failUnless(not p.wait(noError=True))
        self.failUnless(p.procs[0].returncode == 1)

    def testSigPipe(self):
        "test not reading all of pipe output"
        pl = Pipeline([("yes",), ("true",)], "r")
        pl.wait()
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PipelineTests))
    return suite

if __name__ == '__main__':
    unittest.main()
