# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata import dnaOps


class DnaOpsTests(TestCaseBase):

    def testRevCmplStr(self):
        testSeq = "cgcggccatttgtctctt"
        rcSeq = dnaOps.reverseComplement(testSeq)
        self.assertEqual(rcSeq, "aagagacaaatggccgcg")

    def testRevCmplBytes(self):
        testSeq = b"cgcggccatttgtctctt"
        rcSeq = dnaOps.reverseComplement(testSeq)
        self.assertEqual(rcSeq, b"aagagacaaatggccgcg")


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(DnaOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
