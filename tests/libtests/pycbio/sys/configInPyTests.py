# Copyright 2006-2014 Mark Diekhans
import unittest
import os
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.configInPy import evalConfigFunc, evalConfigFile
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import PycbioException


class ConfigInPyTests(TestCaseBase):
    def testConfigFuncCall(self):
        c = evalConfigFunc(self.getInputFile("funcBasic.config.py"))
        self.assertEqual(c.f1, 10)
        self.assertEqual(c.f2, 20)
        self.assertRegex(c.configPyFile, ".*/input/funcBasic.config.py")
        self.assertEqual(c.passedInModule, None)

    def testConfigFuncPassModule(self):
        extraEnv = {"passedInModule": "stuck in a global"}
        c = evalConfigFunc(self.getInputFile("funcBasic.config.py"), extraEnv=extraEnv)
        self.assertEqual(c.f1, 10)
        self.assertEqual(c.f2, 20)
        self.assertRegex(c.configPyFile, ".*/input/funcBasic.config.py")
        self.assertEqual(c.passedInModule, "stuck in a global")

    def testConfigFuncInvalid(self):
        # tests both specifying a different function name and detecting a function that doesn't exist
        with self.assertRaises(PycbioException) as cm:
            evalConfigFunc(self.getInputFile("funcBasic.config.py"), getFuncName="getMissing")
        self.assertRegex(str(cm.exception), "configuration script does not define function getMissing\\(\\)")

    def testConfigFuncArgs(self):
        c = evalConfigFunc(self.getInputFile("funcArgs.config.py"), getFuncArgs=("F1",), getFuncKwargs={"f2": "F2", "f3": "F3"})
        self.assertEqual(c.f1, "F1")
        self.assertEqual(c.f2, "F2")
        self.assertEqual(c.f3, "F3")
        self.assertRegex(c.configPyFile, ".*/input/funcArgs.config.py")

    def _checkFields(self, conf, expect):
        "ensure all expected fields are in configuration"
        for e in expect:
            self.assertTrue(hasattr(conf, e), msg="field not found: {}".format(e))

    def testConfigFileBasic(self):
        c = evalConfigFile(self.getInputFile("objBasic.config.py"))
        self.assertEqual(c.value1, 10)
        self.assertEqual(c.value2, 20)
        self.assertEqual(getattr(c, "_hidden", None), None)
        self.assertRegex(c.configPyFile, ".*/input/objBasic.config.py")
        self.assertEqual(getattr(c, "passedInModule", None), None)
        self.assertEqual(os.path.basename(c.objBasicConfFile), "objBasic.config.py")
        self._checkFields(c, ['configPyFile', 'value1', 'value2'])

    def testConfigFileInclude(self):
        c = evalConfigFile(self.getInputFile("configSub/incl.config.py"))
        self.assertEqual(c.value1, 10)
        self.assertEqual(c.value2, 22)
        self.assertEqual(c.value44, 44)
        self.assertEqual(getattr(c, "_hidden", None), None)
        self.assertRegex(c.configPyFile, ".*/input/configSub/incl.config.py")
        self.assertEqual(getattr(c, "passedInModule", None), None)
        self.assertEqual(os.path.basename(c.objBasicConfFile), "objBasic.config.py")
        self.assertEqual(os.path.basename(c.inclConfFile), "incl.config.py")
        self._checkFields(c, ['configPyFile', 'value1', 'value2'])

    def testConfigFilePassModule(self):
        extraEnv = {"passedInModule": "stuck in a global"}
        c = evalConfigFile(self.getInputFile("objBasic.config.py"), extraEnv=extraEnv)
        self.assertEqual(c.value1, 10)
        self.assertEqual(c.value2, 20)
        self.assertEqual(getattr(c, "_hidden", None), None)
        self.assertRegex(c.configPyFile, ".*/input/objBasic.config.py")
        self.assertEqual(c.passedInModule, "stuck in a global")
        self._checkFields(c, ['configPyFile', "passedInModule", 'value1', 'value2'])


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ConfigInPyTests))
    return ts


if __name__ == '__main__':
    unittest.main()
