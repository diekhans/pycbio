# Copyright 2006-2012 Mark Diekhans
import unittest, sys, re
if __name__ == '__main__':
    sys.path.append("../../../..")

from pycbio.hgbrowser.browserDir import BrowserDir
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
