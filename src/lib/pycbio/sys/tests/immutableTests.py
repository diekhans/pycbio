# Copyright 2006-2012 Mark Diekhans
import unittest, sys, cPickle
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.immutable import Immutable
from pycbio.sys.testCaseBase import TestCaseBase

class ImmutableTests(TestCaseBase):
    def testDictClass(self):
        class DictClass(Immutable):
            def __init__(self, val):
                Immutable.__init__(self)
                self.val = val
                self.mkImmutable()

        obj = DictClass(10)
        with self.assertRaises(TypeError) as cm:
            obj.val = 111
        self.assertEqual(obj.val, 10)

    def testSlotsClass(self):
        class SlotsClass(Immutable):
            __slots__ = ("val", )
            def __init__(self, val):
                Immutable.__init__(self)
                self.val = val
                self.mkImmutable()
        obj = SlotsClass(10)
        with self.assertRaises(TypeError) as cm:
            obj.val = 111
        self.assertEqual(obj.val, 10)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ImmutableTests))
    return suite

if __name__ == '__main__':
    unittest.main()
