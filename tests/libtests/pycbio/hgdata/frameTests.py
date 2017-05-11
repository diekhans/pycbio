# Copyright 2017-2017 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")

from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.frame import Frame

class FrameTests(TestCaseBase):
    def testFrameConstruct(self):
        self.assertEqual(Frame(1), 1)
        self.assertEqual(Frame(-1), -1)

    def testFrameIncr(self):
        self.assertEqual(Frame(1).incr(1), 2)
        self.assertTrue(isinstance(Frame(1)+1, Frame))
        self.assertTrue(isinstance(Frame(1)-1, Frame))
        self.assertEqual(Frame(1)+1, 2)
        self.assertEqual(Frame(1)-1, 0)
        self.assertEqual(Frame(1)+4, 2)
        self.assertEqual(Frame(-1)+1, -1)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(FrameTests))
    return ts

if __name__ == '__main__':
    unittest.main()
