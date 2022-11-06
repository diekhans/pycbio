# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

# from pycbio.hgbrowser.browserDir import BrowserDir
from pycbio.sys.testCaseBase import TestCaseBase

# FIXME: started late, need to write some


class BrowserDirTests(TestCaseBase):
    pass


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(BrowserDirTests))
    return ts


if __name__ == '__main__':
    unittest.main()
