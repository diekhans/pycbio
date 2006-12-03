"tests of CmdRule"

import unittest, sys, os
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.fileOps import ensureFileDir, rmFiles
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun.ExRun import ExRun
from pycbio.exrun.CmdRule import CmdRule, Cmd, File

class CmdSuppliedTests(TestCaseBase):
    "tests of CmdRule with commands supplied to class"

    def testSort1(self):
        "single command to sort a file"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmFiles(ofp.path)
        c = Cmd(("sort", "-n", ifp),
                stdout=ofp)
        er.addRule(CmdRule("sort1", c, (ifp,), (ofp,)))
        er.run()
        self.diffExpected(".txt")

    def testSortPipe(self):
        "pipeline command to sort a file"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmFiles(ofp.path)
        c = Cmd((("sort", "-r", ifp), ("sort", "-nr")),
                stdout=ofp)
        er.addRule(CmdRule("sortPipe", c, (ifp,), (ofp,)))
        er.run()
        self.diffExpected(".txt")

    def testSort2(self):
        "two commands"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmFiles((ofp1.path, ofp2.path))
        c1 = Cmd((("sort", "-r", ifp), ("sort", "-nr")),
                 stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")),
                 stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule("sortPipe", (c1, c2), (ifp,), (ofp1, ofp2)))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2Rules(self):
        "two commands in separate rules"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmFiles((ofp1.path, ofp2.path))
        c1 = Cmd((("sort", "-r", ifp), ("sort", "-nr")),
                 stdout=ofp1)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")),
                 stdin=ofp1, stdout=ofp2)
        er.addRule(CmdRule("count", c2, (ofp1,), (ofp2,)))
        er.addRule(CmdRule("sort", c1, (ifp,), (ofp1,)))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

class CmdSubclassTests(TestCaseBase):
    "tests of CmdRule with subclassing"
    def testSort1(self):
        "single command to sort a file"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, "sort1", ifp, ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call(("sort", "-n", self.ifp), stdout=self.ofp)
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmFiles(ofp.path)
        er.addRule(Sort(ifp, ofp))
        er.run()
        self.diffExpected(".txt")

    def testSortPipe(self):
        "pipeline command to sort a file"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, "sortPipe", ifp, ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call((("sort", "-n", self.ifp),
                           ("sort", "-nr")),
                          stdout=self.ofp)
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmFiles(ofp.path)
        er.addRule(Sort(ifp, ofp))
        er.run()
        self.diffExpected(".txt")


    def testSort2(self):
        "two commands"

        class Sort(CmdRule):
            def __init__(self, ifp, ofp1, ofp2):
                CmdRule.__init__(self, "sort2", ifp, (ofp1, ofp2))
                self.ifp = ifp
                self.ofp1 = ofp1
                self.ofp2 = ofp2
            def run(self):
                self.call((("sort", "-r", self.ifp), ("sort", "-nr")), stdout=self.ofp1)
                self.call((("wc", "-l"), ("sed", "-e", "s/ //g")), stdin=self.ofp1, stdout=self.ofp2)

        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmFiles(ofp.path)
        rmFiles((ofp1.path, ofp2.path))
        er.addRule(Sort(ifp, (ofp1, ofp2)))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")

    def testSort2Rules(self):
        "two commands in separate rules"
        class Sort(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, "sortPipe", ifp, ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call((("sort", "-n", self.ifp),
                           ("sort", "-nr")),
                          stdout=self.ofp)

        class Count(CmdRule):
            def __init__(self, ifp, ofp):
                CmdRule.__init__(self, "countPipe", ifp, ofp)
                self.ifp = ifp
                self.ofp = ofp
            def run(self):
                self.call((("wc", "-l"), ("sed", "-e", "s/ //g")),
                          stdin=self.ifp, stdout=self.ofp)

        
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmFiles((ofp1.path, ofp2.path))
        er.addRule(Count(ofp1, ofp2))
        er.addRule(Sort(ifp, orf1))
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
