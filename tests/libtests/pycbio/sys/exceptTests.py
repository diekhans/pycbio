# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys import PycbioException, pycbioRaiseFrom, pycbioExFormat
from pycbio.sys.testCaseBase import TestCaseBase


class TestExcept(PycbioException):
    pass


class ExceptTests(TestCaseBase):
    def testBasicExcept(self):
        def fn1():
            fn2()

        def fn2():
            fn3()

        def fn3():
            pycbioRaiseFrom(TestExcept("testing 1 2 3"), None)

        # assetRaises doesn't save traceback in exception
        save_ex = None
        try:
            fn1()
        except Exception as ex:
            save_ex = ex
        self.assertIsInstance(save_ex, TestExcept)
        self.assertEqual(str(save_ex), "testing 1 2 3")
        ere = "^Traceback.+testBasicExcept.+fn1\\(\\).+fn2.+TestExcept: testing 1 2 3"
        self.assertRegexDotAll("".join(pycbioExFormat(save_ex)), ere)

    def testChainedExcept(self):  # noqa: C901
        def fn1():
            try:
                fn2()
            except Exception as e:
                pycbioRaiseFrom(TestExcept("in-fn1"), e)

        def fn2():
            fn3()

        def fn3():
            try:
                fn4()
            except Exception as e:
                pycbioRaiseFrom(TestExcept("in-fn3"), e)

        def fn4():
            fn5()

        def fn5():
            fn6()

        def fn6():
            try:
                fn7()
            except Exception as e:
                pycbioRaiseFrom(TestExcept("in-fn6"), e)

        def fn7():
            pycbioRaiseFrom(OSError("OS meltdown"))

        # assetRaises doesn't save traceback in exception
        save_ex = None
        try:
            fn1()
        except Exception as ex:
            save_ex = ex
        self.assertIsInstance(save_ex, TestExcept)
        self.assertEqual(str(save_ex), "in-fn1")
        ere = ("^Traceback .+fn6.+fn7\\(\\).+OSError: OS meltdown"
               ".+Traceback.+fn3.+fn4\\(\\).+fn5\\(\\).+in fn6.+TestExcept: in-fn3")
        self.assertRegexDotAll("".join(pycbioExFormat(save_ex)), ere)

    def testChainedWrap(self):  # noqa: C901
        # what happens if we wrap a non-pycbio exception
        def fn1():
            try:
                fn2()
            except Exception as e:
                pycbioRaiseFrom(TestExcept("in-fn1"), e)

        def fn2():
            fn3()

        def fn3():
            try:
                fn4()
            except Exception as e:
                pycbioRaiseFrom(TestExcept("in-fn3"), e)

        def fn4():
            fn5()

        def fn5():
            fn6()

        def fn6():
            try:
                fn7()
            except Exception as e:
                pycbioRaiseFrom(TestExcept("in-fn6"), e)

        def fn7():
            pycbioRaiseFrom(OSError("OS meltdown"))

        # assetRaises doesn't save traceback in exception
        save_ex = None
        try:
            fn1()
        except Exception as ex:
            save_ex = ex
        self.assertIsInstance(save_ex, TestExcept)
        self.assertEqual(str(save_ex), "in-fn1")
        ere = ("^Traceback .+fn6.+fn7\\(\\).+OSError: OS meltdown"
               ".+Traceback.+fn3.+fn4\\(\\).+fn5\\(\\).+in fn6.+TestExcept: in-fn3")
        self.assertRegexDotAll("".join(pycbioExFormat(save_ex)), ere)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ExceptTests))
    return ts


if __name__ == '__main__':
    unittest.main()
