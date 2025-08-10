# Copyright 2006-2025 Mark Diekhans
import os
import sys
import subprocess
import re
myDir = os.path.normpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(myDir, "../../../../lib"))
from pycbio.sys import testingSupport as ts

def _runTestCmd(request, prog):
    outf = ts.get_test_output_file(request, 'err')
    with open(outf, "w") as outfh:
        subprocess.check_call([sys.executable, os.path.join(myDir, prog)], stderr=outfh)
    with open(outf) as outfh:
        return outfh.read()

def testDumpStack(request):
    errout = _runTestCmd(request, "tryDumpStack.py")
    assert re.search(".*foo2.*", errout)
    assert re.search(".*foo3.*", errout)
    assert re.search(".*stack traces.*", errout)

def testTrace(request):
    errout = _runTestCmd(request, "tryTrace.py")
    assert re.search("foo2()", errout)
    assert re.search("foo3()", errout)
    assert re.search("cnt5 = cnt4 \\+ 1", errout)
