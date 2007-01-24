"tests of CmdRule"

import unittest, sys, os, re
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.fileOps import ensureFileDir, rmFiles
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun import ExRunException, ExRun, CmdRule, Cmd, File

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
        er = ExRun()
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
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmOutput(ofp)
        c = Cmd((("sort", "-r", ifp.getIn()), ("sort", "-nr")), stdout=ofp)
        er.addRule(CmdRule(c, requires=ifp, produces=ofp))
        er.run()
        self.diffExpected(".txt")

    def testSort2(self):
        "two commands"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", ifp.getIn()), ("sort", "-nr")), stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule((c1, c2), requires=ifp))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2Rules(self):
        "two commands in separate rules"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", ifp.getIn()), ("sort", "-nr")), stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule(c2))
        er.addRule(CmdRule(c1, requires=ifp))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2RulesSub(self):
        "two commands in separate rules, with file ref subtitution"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", ifp.getIn()), ("sort", "-nr"), ("tee", ofp1.getOut())), stdout="/dev/null")
        c2 = Cmd((("cat", ofp1.getIn()), ("wc", "-l"), ("sed", "-e", "s/ //g"), ("tee", ofp2.getOut())), stdout="/dev/null")
        er.addRule(CmdRule(c2))
        er.addRule(CmdRule(c1))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

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
        er = ExRun()
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
        er = ExRun()
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

        er = ExRun()
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

        
        er = ExRun()
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
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt.gz"))
        ofp2 = er.getFile(self.getOutputFile(".txt"))
        er.addCmd(["sort", "-r"], stdin=ifp, stdout=ofp1)
        er.addCmd(([ofp1.getCatCmd(), ofp1.getIn()], ["sed", "-e", "s/^/= /"]), stdout=ofp2)
        er.run()
        self.diffExpected(".txt")
        
    def testArgs(self):
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt.gz"))
        ofp2 = er.getFile(self.getOutputFile(".txt"))
        er.addCmd((["sort", "-r", ifp.getIn()], ["tee", ofp1.getOut()]), stdout="/dev/null")
        er.addCmd(([ofp1.getCatCmd(), ofp1.getIn()], ["sed", "-e", "s/^/= /"]), stdout=ofp2.getOut())
        er.run()
        self.diffExpected(".txt")

    def testCmdErr(self):
        "test handling of pipes when process has error"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt.gz"))
        ofp2 = er.getFile(self.getOutputFile(".txt"))
        er.addCmd((["sort", "-r", ifp.getIn()], ["tee", ofp1.getOut()]), stdout="/dev/null")
        er.addCmd(([ofp1.getCatCmd(), ofp1.getIn()], ["false"]), stdout=ofp2.getOut())
        ex = None
        try:
            er.run()
        except OSError, ex:
            exre = ".*process exited with 1: \"false\" in pipeline.*"
            if not re.match(exre, str(ex)):
                self.fail("expected OSError matching: \"" + exre + "\", got: \"" + str(ex) + "\"")
        if ex == None:
            self.fail("expected OSError exception")
            
    def testCmdSigPipe(self):
        "test command recieving SIGPIPE with no error"
        er = ExRun()
        ofp = er.getFile(self.getOutputFile(".txt"))
        er.addCmd((["yes"], ["true"]), stdout=ofp.getOut())
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

