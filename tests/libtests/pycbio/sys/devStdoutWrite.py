"""program that used fileOps.opengz to write to /dev/stdout to test append
behavior"""
import sys
from pycbio.sys import fileOps

with fileOps.opengz("/dev/stdout", "w") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\n")
