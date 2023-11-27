# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.frame import Frame, FRAME1


class FrameTests(TestCaseBase):
    def testConstruct(self):
        # make sure singletons are returned
        f = Frame(1)
        self.assertEqual(f, 1)
        self.assertTrue(f is FRAME1)

        f = Frame("1")
        self.assertEqual(f, 1)
        self.assertEqual(f, Frame(1))
        self.assertTrue(f is FRAME1)

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
        self.assertEqual(Frame.fromPhase('1'), Frame(2))
        self.assertEqual(Frame.fromPhase('.'), None)
        self.assertEqual(Frame.fromPhase(-1), None)
        self.assertEqual(Frame(0).toPhase(), 0)
        self.assertEqual(Frame(1).toPhase(), 2)
        self.assertEqual(Frame(2).toPhase(), 1)

    def testFromFrame(self):
        self.assertEqual(Frame.fromFrame(1), Frame(1))
        self.assertEqual(Frame.fromFrame("1"), Frame(1))
        self.assertEqual(Frame.fromFrame("-1"), None)
        self.assertEqual(Frame.fromFrame("."), None)
        self.assertEqual(Frame.fromFrame(-1), None)

    def testErrors(self):
        with self.assertRaises(ValueError) as context:
            Frame(3)
        self.assertEqual(str(context.exception), "Frame() argument must be in the range 0..2, got 3")
        with self.assertRaises(ValueError) as context:
            Frame(1.0)
        self.assertEqual(str(context.exception), "Frame() takes either a Frame, int, or str value as an argument, got <class 'float'>")


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(FrameTests))
    return ts


if __name__ == '__main__':
    unittest.main()
