"tests of basic functionality"

import unittest, sys, os, time
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys import fileOps
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun import ExRun, File, Rule, Production
from pycbio.exrun.Graph import RuleState

class ProdSet(object):
    "set of file productions and contents; deletes files if they exist"
    
    def __init__(self, exRun, tester, exts):
        self.tester = tester
        self.fps = []
        self.contents = {}
        for ext in exts:
            fp = exRun.getFile(self.tester.getOutputFile(ext))
            fileOps.rmFiles(fp.path)
            self.fps.append(fp)
            self.contents[fp] = ext

    def check(self):
        "verify files and contents"
        for fp in self.fps:
            self.tester.checkContents(fp, self.contents)


class TouchRule(Rule):
    "rule that creates files"
    def __init__(self, name, tester, pset, requires=None):
        Rule.__init__(self, name, requires=requires, produces=pset.fps)
        self.tester = tester
        self.pset = pset
        self.touchCnt = 0

    def _touch(self, fp):
        "create a file product"
        self.tester.failUnless(isinstance(fp, File))
        ext = os.path.splitext(fp.path)[1]
        fileOps.ensureFileDir(fp.getOutPath())
        fh = open(fp.getOutPath(), "w")
        try:
            fh.write(self.pset.contents.get(fp))
        finally:
            fh.close()
            self.touchCnt += 1

    def execute(self):
        "create file products"
        for fp in self.produces:
            self._touch(fp)

class TouchTests(TestCaseBase):
    def checkContents(self, fp, contents={}):
        "contents is a dict of optional values to write"
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
        pset.check()

    def testTwoLevel(self):
        "two levels of requirements"

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
        topRule = TouchRule("top", self, topPset, requires=low1Pset.fps+low2Pset.fps)
        er.addRule(topRule)
        er.run()
        self.failUnlessEqual(low1Rule.touchCnt, 3)
        low1Pset.check()
        self.failUnlessEqual(low2Rule.touchCnt, 3)
        low2Pset.check()
        self.failUnlessEqual(topRule.touchCnt, 3)
        topPset.check()


class CurrentProd(Production):
    "production that is always up-to-date"
    def __init__(self, name):
        Production.__init__(self, name)
    def getTime(self):
        "always returns current time"
        return time.time()

class NeverRunRule(Rule):
    "rule that generates an error if it's run"
    def __init__(self, name, requires=None, produces=None):
        Rule.__init__(self, name, requires=requires, produces=produces)

    def execute(self):
        raise ExRunException("rule should never have been run")

class MiscTests(TestCaseBase):
    def testUptodateProd(self):
        "check that a rule is not run for a current production"
        er = ExRun()
        prod = CurrentProd("neverRunProd")
        er.addNode(prod)
        rule = NeverRunRule("neverRunRule", produces=prod)
        er.addRule(rule)
        er.run()
        self.failIf(rule.state != RuleState.new)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TouchTests))
    suite.addTest(unittest.makeSuite(MiscTests))
    return suite

if __name__ == '__main__':
    unittest.main()
