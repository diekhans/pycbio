# Copyright 2006-2012 Mark Diekhans
import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys import procOps, pipeline
from pycbio.sys.testCaseBase import TestCaseBase

class ProcRunTests(TestCaseBase):
    def testCallSimple(self):
        out = procOps.callProc(["sort", self.getInputFile("simple1.txt")])
        self.assertEqual(out, "five\nfour\none\nsix\nthree\ntwo")

    def testCallKeepNL(self):
        out = procOps.callProc(["sort", self.getInputFile("simple1.txt")], keepLastNewLine=True)
        self.assertEqual(out, "five\nfour\none\nsix\nthree\ntwo\n")

    def testCallErr(self):
        with self.assertRaises(pipeline.ProcException) as cm:
            procOps.callProc(["false"])
        self.assertEqual(str(cm.exception), 'process exited 1: false')

    def testCallLines(self):
        out = procOps.callProcLines(["sort", self.getInputFile("simple1.txt")])
        self.assertEqual(out, ['five', 'four', 'one', 'six', 'three', 'two'])

    def testRunOut(self):
        outf = self.getOutputFile(".txt")
        procOps.runProc(["sort", self.getInputFile("simple1.txt")], stdout=outf)
        self.diffExpected(".txt")

    def BROKEN_testRunFileOut(self):
        with open(self.getOutputFile(".txt"), "w") as outfh:
            procOps.runProc(["sort", self.getInputFile("simple1.txt")], stdout=outfh)
            self.diffExpected(".txt")

    def testRunInOut(self):
        outf = self.getOutputFile(".txt")
        procOps.runProc(["sort"], stdin=self.getInputFile("simple1.txt"), stdout=outf)
        self.diffExpected(".txt")

    # base script that echos to stdout and stderr
    shOutErrCmd = ["sh", "-c", """echo "this is stdout" ; echo "this is stderr" >&2"""]

    def testRunOutErrByNum(self):
        outFile = self.getOutputFile(".stdout")
        errFile = self.getOutputFile(".stderr")
        with open(outFile, "w") as outFh, open(errFile, "w") as errFh:
            procOps.runProc(self.shOutErrCmd, stdout=outFh.fileno(), stderr=errFh.fileno())
        self.diffExpected(".stdout")
        self.diffExpected(".stderr")

    def testRunOutErrByName(self):
        outFile = self.getOutputFile(".stdout")
        errFile = self.getOutputFile(".stderr")
        procOps.runProc(self.shOutErrCmd, stdout=outFile, stderr=errFile)
        self.diffExpected(".stdout")
        self.diffExpected(".stderr")

    def testRunOutErrByFile(self):
        outFile = self.getOutputFile(".stdout")
        errFile = self.getOutputFile(".stderr")
        with open(outFile, "w") as outFh, open(errFile, "w") as errFh:
            procOps.runProc(self.shOutErrCmd, stdout=outFh, stderr=errFh)
        self.diffExpected(".stdout")
        self.diffExpected(".stderr")

    def testRunOutErrSameByFile(self):
        # same file handle for stdout/stderr; make sure it's not closed too soon
        outFile = self.getOutputFile(".stdouterr")
        with open(outFile, "w") as outFh:
            procOps.runProc(self.shOutErrCmd, stdout=outFh, stderr=outFh)
        self.diffExpected(".stdouterr")

    def testRunErr(self):
        with self.assertRaises(pipeline.ProcException) as cm:
            procOps.runProc(["false"], stdin=self.getInputFile("simple1.txt"))
        self.assertEqual(str(cm.exception), 'process exited 1: false')

class ShellQuoteTests(TestCaseBase):
    # set of test words and expected response string
    testData = (
        (["a", "b"], "a b"),
        (["a b", "c$d", "e\\tf"], "a b c$d e\\tf"),
        (["a{b", "c	d", "(ef)", "${hi}", "j<k"], "a{b c	d (ef) ${hi} j<k"),
        )

    def testQuotesBash(self):
        for (words, expect) in self.testData:
            out = procOps.callProc(["sh", "-c", "/bin/echo " + " ".join(procOps.shQuote(words))])
            self.assertEqual(out, expect)
        
    def testQuotesCsh(self):
        # must use /bin/echo, as some csh echos expand backslash sequences
        for (words, expect) in self.testData:
            out = procOps.callProc(["csh", "-c", "/bin/echo " + " ".join(procOps.shQuote(words))])
            self.assertEqual(out, expect)
        

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ProcRunTests))
    ts.addTest(unittest.makeSuite(ShellQuoteTests))
    return ts

if __name__ == '__main__':
    unittest.main()
