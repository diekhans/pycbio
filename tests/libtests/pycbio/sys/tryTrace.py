# Copyright 2006-2025 Mark Diekhans
"""test program that dumps it's own stack"""
import os
import sys
myDir = os.path.normpath(os.path.dirname(sys.argv[0]))
sys.path.insert(0, os.path.join(myDir, "../../../../lib"))
from pycbio.sys.trace import Trace

def foo3():
    cnt = 0
    cnt2 = cnt + 1
    cnt3 = cnt2 + 1
    cnt4 = cnt3 + 1
    cnt5 = cnt4 + 1
    return cnt5

def foo2():
    foo3()

def foo1():
    foo2()

def foo():
    foo1()


trace = Trace(sys.stderr)
trace.enable()
foo()
