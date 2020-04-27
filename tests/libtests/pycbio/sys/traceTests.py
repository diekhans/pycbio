# Copyright 2006-2020 Mark Diekhans
import unittest
import os
import sys
import subprocess
myDir = os.path.normpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(myDir, "../../../../lib"))
from pycbio.sys.testCaseBase import TestCaseBase

class DumpStackTests(TestCaseBase):
    def testDumpStack(self):
        outf = self.getOutputFile('err')
        with open(outf, "w") as outfh:
            subprocess.check_call([sys.executable, os.path.join(myDir, "tryDumpStack.py")], stderr=outfh)
        with open(outf) as outfh:
            errout = outfh.read()
        self.assertRegex(errout, ".*foo2.*")
        self.assertRegex(errout, ".*foo3.*")
        self.assertRegex(errout, ".*stack traces.*")

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(DumpStackTests))
    return ts


if __name__ == '__main__':
    unittest.main()
