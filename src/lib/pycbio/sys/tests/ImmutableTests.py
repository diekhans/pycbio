import unittest, sys, string, cPickle
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.Immutable import Immutable
from pycbio.sys.TestCaseBase import TestCaseBase

class ImmutableTests(TestCaseBase):
    def testDictClass(self):
        class DictClass(Immutable):
            def __init__(self, val):
                self.val = val
                Immutable.__init__(self)
        obj = DictClass(10)
        ex = None
        try:
            obj.val = 111
        except Exception, ex:
            pass
        
        self.failUnlessEqual(obj.val, 10)
        self.failUnless(isinstance(ex, TypeError))

    def testSlotsClass(self):
        class SlotsClass(Immutable):
            __slots__ = ("val", )
            def __init__(self, val):
                self.val = val
                Immutable.__init__(self)
        obj = SlotsClass(10)
        ex = None
        try:
            obj.val = 111
        except Exception, ex:
            pass
        
        self.failUnlessEqual(obj.val, 10)
        self.failUnless(isinstance(ex, TypeError))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ImmutableTests))
    return suite

if __name__ == '__main__':
    unittest.main()
