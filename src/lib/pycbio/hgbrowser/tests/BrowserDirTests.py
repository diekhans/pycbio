# Copyright 2006-2012 Mark Diekhans
import unittest, sys, re
if __name__ == '__main__':
    sys.path.append("../../..")

from pycbio.hgbrowser.BrowserDir import BrowserDir
from pycbio.sys.TestCaseBase import TestCaseBase

# FIXME: started late, need to write some

class BrowserDirTests(TestCaseBase):
    pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BrowserDirTests))
    return suite

if __name__ == '__main__':
    unittest.main()
