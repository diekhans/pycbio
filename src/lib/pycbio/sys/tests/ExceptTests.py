import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys import PycbioException
from pycbio.sys.TestCaseBase import TestCaseBase

class TestExcept(PycbioException):
    pass

class ExceptTests(TestCaseBase):
    def testBasicExcept(self):
        def fn1():
            fn2()
        def fn2():
            fn3()
        def fn3():
            raise TestExcept("testing 1 2 3")

        ex = None
        try:
            fn1()
        except Exception, e:
            ex = e
        self.failUnless(ex != None)
        self.failUnlessEqual(str(ex), "testing 1 2 3")
        self.failUnlessMatch(ex.format(), """^testing 1 2 3.+in testBasicExcept.+fn1\(\).+fn2\(\).+fn3\(\).+raise TestExcept\("testing 1 2 3"\)\n$""")
        
    def testChainedExcept(self):
        def fn1():
            try:
                fn2()
            except Exception,e:
                raise TestExcept("in-fn1", e)
        def fn2():
            fn3()
        def fn3():
            try:
                fn4()
            except Exception,e:
                raise TestExcept("in-fn3", e)
        def fn4():
            fn5()
        def fn5():
            fn6()
        def fn6():
            try:
                fn7()
            except Exception,e:
                raise TestExcept("in-fn6", e)
        def fn7():
            raise OSError("OS meltdown")

        ex = None
        try:
            fn1()
        except Exception, e:
            ex = e
        self.failUnless(ex != None)
        self.failUnlessEqual(str(ex), "in-fn1, caused by in-fn3, caused by OS meltdown")
        print ex.format()
        #self.failUnlessMatch(ex.format(), """^testing 1 2 3.+in testBasicExcept.+self.fn1\(\).+self.fn2\(\).+self.fn3\(\).+raise TestExcept\("testing 1 2 3"\)\n$""")
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExceptTests))
    return suite

if __name__ == '__main__':
    unittest.main()
