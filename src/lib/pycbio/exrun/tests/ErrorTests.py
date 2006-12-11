"test of error conditions"

import unittest, sys, os
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun.ExRun import ExRun,ExRunException
from pycbio.exrun.Graph import Rule, CycleException
from pycbio.sys import fileOps

# FIXME add:
#  dup production test

class ErrorRule(Rule):
    "rule that should never be run"
    def __init__(self, name, requires=None, produces=None):
        Rule.__init__(self, name, requires, produces)

    def execute(self):
        raise Exception("rule should never be run: " + str(self))

class TouchRule(Rule):
    "rule that creates files"
    def __init__(self, name, tester, requires=None, produces=None):
        Rule.__init__(self, name, requires=requires, produces=produces)
        self.tester = tester

    def execute(self):
        "create file product"
        for fp in self.produces:
            fileOps.ensureFileDir(fp.path)
            open(fp.path, "w").close()

class ErrorTests(TestCaseBase):
    def testCycleAll(self):
        "all nodes in a cycle (no entry)"
        id = self.getId()
        ex = None
        try:
            er = ExRun()
            # use id so file path doesn't vary with run directory
            f1 = er.getFile(id + ".file1")
            f2 = er.getFile(id + ".file2")
            f3 = er.getFile(id + ".file3")
            er.addRule(ErrorRule("cycleAll1", f1, f2))
            er.addRule(ErrorRule("cycleAll2", f2, f3))
            er.addRule(ErrorRule("cycleAll3", f3, f1))
            er.run()
        except CycleException, ex:
            self.failUnlessEqual(str(ex), "cycle detected:\n  cycleAll3 ->\n  ErrorTests.ErrorTests.testCycleAll.file3 ->\n  cycleAll2 ->\n  ErrorTests.ErrorTests.testCycleAll.file2 ->\n  cycleAll1 ->\n  ErrorTests.ErrorTests.testCycleAll.file1 ->")
        if ex == None:
            self.fail("expected CycleException")
        
    def testCycle(self):
        "entry node and cycle"
        # can't build this graph due to linking sanity checks            
        id = self.getId()
        ex = None
        try:
            er = ExRun()
            # use id so file path doesn't vary with run directory
            f1 = er.getFile(id + ".file1")
            f2 = er.getFile(id + ".file2")
            f3 = er.getFile(id + ".file3")
            er.addRule(ErrorRule("cycle1", f1, f2))
            er.addRule(ErrorRule("cycle2", f2, f3))
            er.addRule(ErrorRule("cycle3", f3, f2))
            er.run()
        except ExRunException, ex:
            self.failUnlessEqual(str(ex), "Production ErrorTests.ErrorTests.testCycle.file2 already linked to it's produces, attempt to add: cycle3")
        if ex == None:
            self.fail("expected ExRunException")

    def testNoRule(self):
        "no rule to make a production"
        ex = None
        try:
            er = ExRun()
            f1 = er.getFile(self.getOutputFile(".file1"))
            f2 = er.getFile(self.getOutputFile(".file2"))
            f3 = er.getFile(self.getId() + ".file3")
            er.addRule(TouchRule("noRule1", self, f3, f2))
            er.addRule(TouchRule("noRule2", self, f2, f1))
            er.run()
        except ExRunException, ex:
            self.failUnlessEqual(str(ex), "No rule to build production(s): ErrorTests.ErrorTests.testNoRule.file3")
        if ex == None:
            self.fail("expected ExRunException")
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ErrorTests))
    return suite

if __name__ == '__main__':
    unittest.main()
