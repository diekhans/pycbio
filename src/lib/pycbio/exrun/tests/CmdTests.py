"tests of CmdRule"

import unittest, sys, os
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.fileOps import ensureFileDir, rmFiles
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun.ExRun import ExRun
from pycbio.exrun.CmdRule import CmdRule, Cmd, File

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
        c = Cmd((("sort", "-r", ifp), ("sort", "-nr")), stdout=ofp)
        er.addRule(CmdRule(c, (ifp,), (ofp,)))
        er.run()
        self.diffExpected(".txt")

    def testSort2(self):
        "two commands"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmOutput(ofp1, ofp2)
        c1 = Cmd((("sort", "-r", ifp), ("sort", "-nr")), stdout=ofp1)
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
        c1 = Cmd((("sort", "-r", ifp), ("sort", "-nr")), stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule(c2))
        er.addRule(CmdRule(c1, requires=ifp))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

class CmdSubclassTests(TestCaseBase):
    "tests of CmdRule with subclassing"
    def testSort1(self):
        "single command to sort a file"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, None, ifp, ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(Cmd(("sort", "-n", self.ifp.getInput()), stdout=self.ofp))
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
                CmdRule.__init__(self, None, ifp, ofp)
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
                CmdRule.__init__(self, None, ifp, (ofp1, ofp2))
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
                CmdRule.__init__(self, None, ifp, ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(Cmd((("sort", "-n", self.ifp), ("sort", "-nr")),
                              stdout=self.ofp))

        class Count(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, None, ifp, ofp)
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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CmdSuppliedTests))
    suite.addTest(unittest.makeSuite(CmdSubclassTests))
    return suite

if __name__ == '__main__':
    unittest.main()
