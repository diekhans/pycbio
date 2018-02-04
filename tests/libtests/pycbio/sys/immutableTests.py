# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.immutable import Immutable
from pycbio.sys.testCaseBase import TestCaseBase


class ImmutableTests(TestCaseBase):
    def testDictClass(self):
        class DictClass(Immutable):
            def __init__(self, val):
                super(DictClass, self).__init__()
                self.val = val
                self.mkImmutable()

        obj = DictClass(10)
        with self.assertRaises(TypeError):
            obj.val = 111
        self.assertEqual(obj.val, 10)

    def testSlotsClass(self):
        class SlotsClass(Immutable):
            __slots__ = ("val", )

            def __init__(self, val):
                super(SlotsClass, self).__init__()
                self.val = val
                self.mkImmutable()
        obj = SlotsClass(10)
        with self.assertRaises(TypeError):
            obj.val = 111
        self.assertEqual(obj.val, 10)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ImmutableTests))
    return ts


if __name__ == '__main__':
    unittest.main()
