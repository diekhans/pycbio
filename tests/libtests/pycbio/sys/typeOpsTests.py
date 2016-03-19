# Copyright 2015-2015 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.extend(["../../..", "../../../.."])
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import typeOps


class TypeOpsTests(TestCaseBase):
    def testAnnon(self):
        ao = typeOps.annon(a=10, b=20, fred="spaced out")
        self.assertEquals(ao.a, 10)
        self.assertEquals(ao.b, 20)
        self.assertEquals(str(ao), "a=10, b=20, fred='spaced out'")


# FIXME: many more tests needed

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(TypeOpsTests))
    return ts

if __name__ == '__main__':
    unittest.main()
