# Copyright 2006-2014 Mark Diekhans
import unittest
import sys
import re
if __name__ == '__main__':
    sys.path.extend(["../../..", "../../../.."])
from pycbio.sys.configInPy import evalConfigFunc, evalConfigObj
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import PycbioException


class ConfigInPyTests(TestCaseBase):
    def testConfigFuncCall(self):
        c = evalConfigFunc(self.getInputFile("funcBasic.config.py"))
        self.assertEqual(c.f1, 10)
        self.assertEqual(c.f2, 20)
        self.assertRegexpMatches(c.configPyFile, ".*/input/funcBasic.config.py")
        self.assertEqual(c.passedInModule, None)

    def testConfigFuncPassModule(self):
        extraEnv = {"passedInModule": "stuck in a global"}
        c = evalConfigFunc(self.getInputFile("funcBasic.config.py"), extraEnv=extraEnv)
        self.assertEqual(c.f1, 10)
        self.assertEqual(c.f2, 20)
        self.assertRegexpMatches(c.configPyFile, ".*/input/funcBasic.config.py")
        self.assertEqual(c.passedInModule, "stuck in a global")

    def testConfigFuncInvalid(self):
        # tests both specifying a different function name and detecting a function that doesn't exist
        with self.assertRaises(PycbioException) as cm:
            evalConfigFunc(self.getInputFile("funcBasic.config.py"), getFuncName="getMissing")
        self.assertRegexpMatches(cm.exception.message, "configuration script does not define function getMissing\\(\\)")

    def testConfigFuncArgs(self):
        c = evalConfigFunc(self.getInputFile("funcArgs.config.py"), getFuncArgs=("F1",), getFuncKwargs={"f2": "F2", "f3": "F3"})
        self.assertEqual(c.f1, "F1")
        self.assertEqual(c.f2, "F2")
        self.assertEqual(c.f3, "F3")
        self.assertRegexpMatches(c.configPyFile, ".*/input/funcArgs.config.py")

    def __getFields(self, c):
        "return non-reserved name fields"
        return sorted([f for f in dir(c) if not re.match("^__.*__", f)])

    def testConfigObjBasic(self):
        c = evalConfigObj(self.getInputFile("objBasic.config.py"))
        self.assertEqual(c.value1, 10)
        self.assertEqual(c.value2, 20)
        self.assertEqual(getattr(c, "_hidden", None), None)
        self.assertRegexpMatches(c.configPyFile, ".*/input/objBasic.config.py")
        self.assertEqual(getattr(c, "passedInModule", None), None)
        self.assertEqual(self.__getFields(c), ['configPyFile', 'value1', 'value2'])

    def testConfigObjPassModule(self):
        extraEnv = {"passedInModule": "stuck in a global"}
        c = evalConfigObj(self.getInputFile("objBasic.config.py"), extraEnv=extraEnv)
        self.assertEqual(c.value1, 10)
        self.assertEqual(c.value2, 20)
        self.assertEqual(getattr(c, "_hidden", None), None)
        self.assertRegexpMatches(c.configPyFile, ".*/input/objBasic.config.py")
        self.assertEqual(c.passedInModule, "stuck in a global")
        self.assertEqual(self.__getFields(c), ['configPyFile', "passedInModule", 'value1', 'value2'])


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ConfigInPyTests))
    return ts

if __name__ == '__main__':
    unittest.main()
