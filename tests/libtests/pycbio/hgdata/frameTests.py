# Copyright 2017-2017 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.frame import Frame


class FrameTests(TestCaseBase):
    def testConstruct(self):
        self.assertEqual(Frame(1), 1)
        self.assertEqual(Frame("1"), Frame(1))

    def testIncr(self):
        self.assertEqual(Frame(1).incr(1), 2)
        self.assertTrue(isinstance(Frame(1) + 1, Frame))
        self.assertTrue(isinstance(Frame(1) - 1, Frame))
        self.assertEqual(Frame(1) + 1, 2)
        self.assertEqual(Frame(1) - 1, 0)
        self.assertEqual(Frame(1) + 4, 2)
        self.assertEqual(Frame(1) - 6, 1)
        self.assertEqual(Frame(1) - 7, 0)

    def testPhase(self):
        self.assertEqual(Frame.fromPhase(0), Frame(0))
        self.assertEqual(Frame.fromPhase(1), Frame(2))
        self.assertEqual(Frame.fromPhase(2), Frame(1))
        self.assertEqual(Frame(0).toPhase(), 0)
        self.assertEqual(Frame(1).toPhase(), 2)
        self.assertEqual(Frame(2).toPhase(), 1)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(FrameTests))
    return ts


if __name__ == '__main__':
    unittest.main()
