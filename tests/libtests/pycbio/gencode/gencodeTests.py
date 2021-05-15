# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.gencode import biotypes, gencodeTags  # noqa:F401

class GencodeTests(TestCaseBase):
    # asserts in biotypes test a lot, should move into here
    pass


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(GencodeTests))
    return ts


if __name__ == '__main__':
    unittest.main()
