# Copyright 2015-2015 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import typeOps

# FIXME: many more tests needed


class TypeOpsTests(TestCaseBase):
    def testAnnon(self):
        ao = typeOps.annon(a=10, b=20, fred="spaced out")
        self.assertEqual(ao.a, 10)
        self.assertEqual(ao.b, 20)
        self.assertEqual(str(ao), "a=10, b=20, fred='spaced out'")

    def testAttrdic(self):
        class ODict(object):
            def __init__(self):
                self.f = 100

        class OSlots(object):
            __slots__ = ("f")

            def __init__(self):
                self.f = 101

        odict = ODict()
        self.assertEqual(typeOps.attrdict(odict)['f'], 100)
        oslots = OSlots()
        self.assertEqual(typeOps.attrdict(oslots)['f'], 101)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(TypeOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
