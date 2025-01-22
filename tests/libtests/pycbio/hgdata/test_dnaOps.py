# Copyright 2006-2025 Mark Diekhans
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

    def testIsValidStr(self):
        self.assertTrue(dnaOps.isValidBase('a'))
        self.assertTrue(dnaOps.isValidBase('C'))
        self.assertFalse(dnaOps.isValidBase('@'))

    def testIsValidByte(self):
        self.assertTrue(dnaOps.isValidBase(b'a'))
        self.assertTrue(dnaOps.isValidBase(b'C'))
        self.assertFalse(dnaOps.isValidBase(b'@'))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(DnaOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
