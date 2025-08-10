# Copyright 2006-2025 Mark Diekhans
import pytest
import os
import sys
import re
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.configInPy import evalConfigFunc, evalConfigFile
import pycbio.sys.testingSupport as ts
from pycbio import PycbioException


def testConfigFuncCall(request):
    c = evalConfigFunc(ts.get_test_input_file(request, "funcBasic.config.py"))
    assert c.f1 == 10
    assert c.f2 == 20
    assert re.search(".*/input/funcBasic.config.py", c.configPyFile)
    assert c.passedInModule is None

def testConfigFuncPassModule(request):
    extraEnv = {"passedInModule": "stuck in a global"}
    c = evalConfigFunc(ts.get_test_input_file(request, "funcBasic.config.py"), extraEnv=extraEnv)
    assert c.f1 == 10
    assert c.f2 == 20
    assert re.search(".*/input/funcBasic.config.py", c.configPyFile)
    assert c.passedInModule == "stuck in a global"

def testConfigFuncInvalid(request):
    # tests both specifying a different function name and detecting a function that doesn't exist
    with pytest.raises(PycbioException) as cm:
        evalConfigFunc(ts.get_test_input_file(request, "funcBasic.config.py"), getFuncName="getMissing")
    assert re.search("configuration script does not define function getMissing\\(\\)",
                     str(cm.value))

def testConfigFuncArgs(request):
    c = evalConfigFunc(ts.get_test_input_file(request, "funcArgs.config.py"), getFuncArgs=("F1",), getFuncKwargs={"f2": "F2", "f3": "F3"})
    assert c.f1 == "F1"
    assert c.f2 == "F2"
    assert c.f3 == "F3"
    assert re.search(".*/input/funcArgs.config.py", c.configPyFile)

def _checkFields(conf, expect):
    "ensure all expected fields are in configuration"
    for e in expect:
        assert hasattr(conf, e), f"field not found: {e}"

def testConfigFileBasic(request):
    c = evalConfigFile(ts.get_test_input_file(request, "objBasic.config.py"))
    assert c.value1 == 10
    assert c.value2 == 20
    assert getattr(c, "_hidden", None) is None
    assert re.search(".*/input/objBasic.config.py", c.configPyFile)
    assert getattr(c, "passedInModule", None) is None
    assert os.path.basename(c.objBasicConfFile) == "objBasic.config.py"
    _checkFields(c, ['configPyFile', 'value1', 'value2'])

def testConfigFileInclude(request):
    c = evalConfigFile(ts.get_test_input_file(request, "configSub/incl.config.py"))
    assert c.value1 == 10
    assert c.value2 == 22
    assert c.value44 == 44
    assert getattr(c, "_hidden", None) is None
    assert re.search(".*/input/configSub/incl.config.py", c.configPyFile)
    assert getattr(c, "passedInModule", None) is None
    assert os.path.basename(c.objBasicConfFile) == "objBasic.config.py"
    assert os.path.basename(c.inclConfFile) == "incl.config.py"
    _checkFields(c, ['configPyFile', 'value1', 'value2'])

def testConfigFilePassModule(request):
    extraEnv = {"passedInModule": "stuck in a global"}
    c = evalConfigFile(ts.get_test_input_file(request, "objBasic.config.py"), extraEnv=extraEnv)
    assert c.value1 == 10
    assert c.value2 == 20
    assert getattr(c, "_hidden", None) is None
    assert re.search(".*/input/objBasic.config.py", c.configPyFile)
    assert c.passedInModule == "stuck in a global"
    _checkFields(c, ['configPyFile', "passedInModule", 'value1', 'value2'])
