"test of basic functionality"

import unittest, sys, os
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.fileOps import ensureFileDir, rmFiles
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun.ExRun import ExRun, File, CmdRule, Cmd
from pycbio.exrun.Graph import Rule

class ProdSet(object):
    "set of file productions and contents; deletes files if they exist"
    
    def __init__(self, exRun, tester, exts):
        self.tester = tester
        self.fps = []
        self.contents = {}
        for ext in exts:
            fp = exRun.getFile(self.tester.getOutputFile(ext))
            rmFiles(fp.path)
            self.fps.append(fp)
            self.contents[fp] = ext

    def check(self):
        "verify files and contents"
        for fp in self.fps:
            self.tester.checkContents(fp, self.contents)


class TouchRule(Rule):
    "rule that creates files"
    def __init__(self, id, tester, pset, requires=None):
        "contents is a dict of optional values to write"
        Rule.__init__(self, id, pset.fps, requires)
        self.tester = tester
        self.pset = pset
        self.touchCnt = 0

    def run(self):
        "create file products"
        for p in self.produces:
            fp = p.prev
            self.tester.failUnless(isinstance(fp, File))
            ext = os.path.splitext(fp.path)[1]
            self.tester.createOutputFile(ext, self.pset.contents.get(fp))
            self.touchCnt += 1

class TouchTests(TestCaseBase):
    def checkContents(self, fp, contents={}):
        ext = os.path.splitext(fp.path)[1]
        self.verifyOutputFile(ext, contents.get(fp))

    def testSimple(self):
        "rule with no requirements "

        # rule creates three files with known content
        er = ExRun()
        pset = ProdSet(er, self, (".out1", ".out2", ".out3"))
        rule = TouchRule("simple", self, pset)
        er.addRule(rule)
        er.run()
        self.failUnlessEqual(rule.touchCnt, 3)
        pset.check()

        # try again, nothing should be made this time
        rule.touchCnt = 0
        er.run()
        self.failUnlessEqual(rule.touchCnt, 0)

    def testTwoLevel(self):
        "two levels of requirements "

        er = ExRun()

        # lower level, 2 productions and rules
        low1Pset = ProdSet(er, self, (".low1a", ".low1b", ".low1c"))
        low1Rule = TouchRule("low1Rule", self, low1Pset)
        er.addRule(low1Rule)
        low2Pset = ProdSet(er, self, (".low2a", ".low2b", ".low2c"))
        low2Rule = TouchRule("low2Rule", self, low2Pset)
        er.addRule(low2Rule)
        
        # top level, dependent on intermediates
        topPset = ProdSet(er, self, (".top1", ".top2", ".top3"))
        topRule = TouchRule("top", self, topPset, low1Pset.fps+low2Pset.fps)
        er.run()
        self.failUnlessEqual(low1Rule.touchCnt, 3)
        low1Pset.check()
        self.failUnlessEqual(low2Rule.touchCnt, 3)
        low2Pset.check()
        self.failUnlessEqual(topRule.touchCnt, 3)
        topPset.check()

class CmdTests(TestCaseBase):
    def testSort1(self):
        "single command to sort a file"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmFiles(ofp.path)
        c = Cmd(("sort", "-n", ifp.path),
                stdout=ofp.path)
        er.addRule(CmdRule("sort1", c, (ofp,), (ifp,)))
        er.run()
        self.diffExpected(".txt")

    def testSortPipe(self):
        "pipeline command to sort a file"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp = er.getFile(self.getOutputFile(".txt"))
        rmFiles(ofp.path)
        c = Cmd((("sort", "-r", ifp.path), ("sort", "-nr")),
                stdout=ofp.path)
        er.addRule(CmdRule("sortPipe", c, (ofp,), (ifp,)))
        er.run()
        self.diffExpected(".txt")

    def testSort2(self):
        "two commands"
        er = ExRun()
        ifp = er.getFile(self.getInputFile("numbers.txt"))
        ofp1 = er.getFile(self.getOutputFile(".txt"))
        ofp2 = er.getFile(self.getOutputFile(".linecnt"))
        rmFiles((ofp1.path, ofp2.path))
        c1 = Cmd((("sort", "-r", ifp.path), ("sort", "-nr")),
                 stdout=ofp1.path)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")),
                 stdin=ofp1.path, stdout=ofp2.path)
        er.addRule(CmdRule("sortPipe", (c1, c2), (ofp1, ofp2), (ifp,)))
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
        c1 = Cmd((("sort", "-r", ifp.path), ("sort", "-nr")),
                 stdout=ofp1.path)
        c2 = Cmd((("wc", "-l"), ("sed", "-e", "s/ //g")),
                 stdin=ofp1.path, stdout=ofp2.path)
        er.addRule(CmdRule("count", c2, (ofp2,), (ofp1,)))
        er.addRule(CmdRule("sort", c1, (ofp1,), (ifp,)))
        er.run()
        self.diffExpected(".txt")
        self.diffExpected(".linecnt")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TouchTests))
    suite.addTest(unittest.makeSuite(CmdTests))
    return suite

if __name__ == '__main__':
    unittest.main()
