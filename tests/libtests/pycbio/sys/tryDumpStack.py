# Copyright 2006-2012 Mark Diekhans
"""test program that dumps it's own stack"""
import os
import sys
import signal
myDir = os.path.normpath(os.path.dirname(sys.argv[0]))
sys.path.insert(0, os.path.join(myDir, "../../../../lib"))
from pycbio.sys.trace import enableDumpStack

def foo3():
    os.kill(os.getpid(), signal.SIGUSR1)

def foo2():
    foo3()

def foo1():
    foo2()

def foo():
    foo1()


enableDumpStack()
foo()
