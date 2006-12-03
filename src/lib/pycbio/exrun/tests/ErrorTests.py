"test of error conditions"

import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.exrun.ExRun import ExRun,ExRunException
from pycbio.exrun.Graph import Rule,CycleException

# FIXME add:
#  dup production test

class ErrorRule(Rule):
    "rule that should never be run"
    def __init__(self, id, requires=None, produces=None):
        Rule.__init__(self, id, requires, produces)

    def run(self):
        raise Exception("rule should never be run: " + str(self))

class GraphTests(TestCaseBase):
    def testCycleAll(self):
        "all nodes in a cycle (no entry)"
        id = self.getId()
        er = ExRun()
        # use id so file path doesn't vary with run directory
        f1 = er.getFile(id + ".file1")
        f2 = er.getFile(id + ".file2")
        f3 = er.getFile(id + ".file3")
        er.addRule(ErrorRule("rule1", f1, f2))
        er.addRule(ErrorRule("rule2", f2, f3))
        er.addRule(ErrorRule("rule3", f3, f1))
        ex = None
        try:
            er.run()
        except CycleException, ex:
            self.failUnlessEqual(str(ex), "cycle detected:\n  rule1 ->\n  ErrorTests.GraphTests.testCycleAll.file2 ->\n  rule2 ->\n  ErrorTests.GraphTests.testCycleAll.file3 ->\n  rule3 ->\n  ErrorTests.GraphTests.testCycleAll.file1 ->")
        if ex == None:
            self.fail("expected CycleException")
        
    def testCycle(self):
        "entry node and cycle"
        id = self.getId()
        er = ExRun()
        # use id so file path doesn't vary with run directory
        f1 = er.getFile(id + ".file1")
        f2 = er.getFile(id + ".file2")
        f3 = er.getFile(id + ".file3")
        er.addRule(ErrorRule("rule1", f1, f2))
        er.addRule(ErrorRule("rule2", f2, f3))
        er.addRule(ErrorRule("rule3", f3, f2))
        ex = None
        try:
            er.run()
        except CycleException, ex:
            self.failUnlessEqual(str(ex),"cycle detected:\n  rule2 ->\n  ErrorTests.GraphTests.testCycle.file3 ->\n  rule3 ->\n  ErrorTests.GraphTests.testCycle.file2 ->")
        if ex == None:
            self.fail("expected CycleException")

    def testNoRule(self):
        "no rule to make a production"

        id = self.getId()
        er = ExRun()
        # use id so file path doesn't vary with run directory
        f1 = er.getFile(id + ".file1")
        f2 = er.getFile(id + ".file2")
        f3 = er.getFile(id + ".file3")
        er.addRule(ErrorRule("rule1", f3, f2))
        er.addRule(ErrorRule("rule2", f2, f1))
        ex = None
        try:
            er.run()
        except ExRunException, ex:
            self.failUnlessEqual(str(ex),"no rule to build: ErrorTests.GraphTests.testNoRule.file1")
        if ex == None:
            self.fail("expected ExRunException")
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GraphTests))
    return suite

if __name__ == '__main__':
    unittest.main()
