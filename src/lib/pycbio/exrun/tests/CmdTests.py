"tests of CmdRule"

import unittest, sys, os, re
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.fileOps import ensureFileDir, rmFiles
from pycbio.sys.Pipeline import ProcException
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun import ExRunException, ExRun, CmdRule, Cmd, File, FileIn, FileOut, Verb

# change this for debugging:
verbFlags=None
#verbFlags=set((Verb.error, Verb.trace, Verb.details))

def rmOutput(*files):
    "delete output files, which can be specified as strings or File objects"
    for f in files:
        if isinstance(f, File):
            rmFiles(f.path)
        else:
            rmFiles(f)

class CmdSuppliedTests(TestCaseBase):
    "tests of CmdRule with commands supplied to class"

    def testSort1(self):
        "single command to sort a file"
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmOutput(ofp)
        # auto add requires and produces
        c = Cmd(("sort", "-n"), stdin=ifp, stdout=ofp)
        er.addRule(CmdRule(c))
        er.run()
        self.diffExpected(".txt")

    def testSortPipe(self):
        "pipeline command to sort a file"
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmOutput(ofp)
        c = Cmd((("sort", "-r", FileIn(ifp)), ("sort", "-nr")), stdout=ofp)
        er.addRule(CmdRule(c, requires=ifp, produces=ofp))
        er.run()
        self.diffExpected(".txt")

    def testSort2(self):
        "two commands"
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", FileIn(ifp)), ("sort", "-nr")), stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule((c1, c2), requires=ifp))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2Rules(self):
        "two commands in separate rules"
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", FileIn(ifp)), ("sort", "-nr")), stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule(c2))
        er.addRule(CmdRule(c1, requires=ifp))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2RulesSub(self):
        "two commands in separate rules, with file ref subtitution"
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", FileIn(ifp)), ("sort", "-nr"), ("tee", FileOut(ofp1))), stdout="/dev/null")
        c2 = Cmd((("cat", FileIn(ofp1)), ("wc", "-l"), ("sed", "-e", "s/ //g"), ("tee", FileOut(ofp2))), stdout="/dev/null")
        er.addRule(CmdRule(c2))
        er.addRule(CmdRule(c1))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testFilePrefix(self):
        "test prefixes to FileIn/FileOut"
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmOutput(ofp)
        c = Cmd(("dd", "if="+FileIn(ifp), "of="+FileOut(ofp)))
        er.addRule(CmdRule(c))
        er.run()
        self.diffExpected(".txt")

class CmdSubclassTests(TestCaseBase):
    "tests of CmdRule with subclassing"
    def testSort1(self):
        "single command to sort a file"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, requires=ifp, produces=ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(Cmd(("sort", "-n", self.ifp.getInPath()), stdout=self.ofp))
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmOutput(ofp)
        er.addRule(Sort(ifp, ofp))
        er.run()
        self.diffExpected(".txt")

    def testSortPipe(self):
        "pipeline command to sort a file"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, requires=ifp, produces=ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(Cmd((("sort", "-n", self.ifp), ("sort", "-nr")),
                              stdout=self.ofp))
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmOutput(ofp)
        er.addRule(Sort(ifp, ofp))
        er.run()
        self.diffExpected(".txt")

    def testSort2(self):
        "two commands"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp1, ofp2):
                CmdRule.__init__(self, requires=ifp, produces=(ofp1, ofp2))
                self.ifp = ifp
                self.ofp1 = ofp1
                self.ofp2 = ofp2
            def run(self):
                self.call(Cmd((("sort", "-r", self.ifp), ("sort", "-nr")), stdout=self.ofp1))
                self.call(Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=self.ofp1, stdout=self.ofp2))

        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        er.addRule(Sort(ifp, ofp1, ofp2))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2Rules(self):
        "two commands in separate rules"
        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, requires=ifp, produces=ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(Cmd((("sort", "-n", self.ifp), ("sort", "-nr")),
                              stdout=self.ofp))

        class Count(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, requires=ifp, produces=ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")),
                              stdin=self.ifp, stdout=self.ofp))

        
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        er.addRule(Count(ofp1, ofp2))
        er.addRule(Sort(ifp, ofp1))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

class CmdCompressTests(TestCaseBase):
    "tests of CmdRule with automatic compression"

    def testStdio(self):
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt.gz"))
        ofp2 = er.getFile(self.getOutputFile(".txt"))
        er.addCmd(["sort", "-r"], stdin=ifp, stdout=ofp1)
        er.addCmd((["zcat", FileIn(ofp1, autoDecompress=False)], ["sed", "-e", "s/^/= /"]), stdout=ofp2)
        er.run()
        self.diffExpected(".txt")
        
    def testArgs(self):
        er = ExRun(verbFlags=verbFlags)
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt.gz"))
        ofp2 = er.getFile(self.getOutputFile(".txt"))
        er.addCmd((["sort", "-r", FileIn(ifp)], ["tee", FileOut(ofp1)]), stdout="/dev/null")
        er.addCmd(["sed", "-e", "s/^/= /", FileIn(ofp1)], stdout=FileOut(ofp2))
        er.run()
        self.diffExpected(".txt")

    def testCmdErr(self):
        "test handling of pipes when process has error"
        er = ExRun(verbFlags=set())
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt.gz"))
        ofp2 = er.getFile(self.getOutputFile(".txt"))
        er.addCmd((["sort", "-r", FileIn(ifp)], ["tee", FileOut(ofp1)]), stdout="/dev/null")
        er.addCmd((["zcat", FileIn(ofp1, autoDecompress=False)], ["false"]), stdout=FileOut(ofp2))
        ex = None
        try:
            er.run()
        except ProcException, ex:
            exre = "process exited 1:\nfalse"
            if not re.match(exre, str(ex)):
                self.fail("expected ProcException matching: \"" + exre + "\", got: \"" + str(ex) + "\"")
        if ex == None:
            self.fail("expected ProcException")
            
    def testCmdSigPipe(self):
        "test command recieving SIGPIPE with no error"
        er = ExRun(verbFlags=verbFlags)
        ofp = er.getFile(self.getOutputFile(".txt"))
        er.addCmd((["yes"], ["true"]), stdout=FileOut(ofp))
        ex = None
        er.run()
            
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CmdSuppliedTests))
    suite.addTest(unittest.makeSuite(CmdSubclassTests))
    suite.addTest(unittest.makeSuite(CmdCompressTests))
    return suite

if __name__ == '__main__':
    unittest.main()

