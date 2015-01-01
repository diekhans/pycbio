# Copyright 2006-2012 Mark Diekhans
import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.tsv import TabFile,TabFileReader
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.autoSql import intArrayType

class TabFileTests(TestCaseBase):
    typesNumRows = 4
    typesNumCols = 4

    def checkRowsCols(self, rows, expectNumRows, expectNumCols):
        numRows = 0
        for row in rows:
            self.assertEqual(len(row), expectNumCols)
            numRows += 1
        self.assertEqual(numRows, expectNumRows)
        
    def testTable(self):
        tbl = TabFile(self.getInputFile("types.tsv"))
        self.checkRowsCols(tbl, self.typesNumRows, self.typesNumCols)

    def testTableComments(self):
        tbl = TabFile(self.getInputFile("typesComment.tsv"), hashAreComments=True)
        self.checkRowsCols(tbl, self.typesNumRows-1, self.typesNumCols)

    def testReader(self):
        rows = []
        for row in TabFileReader(self.getInputFile("types.tsv")):
            rows.append(row)
        self.checkRowsCols(rows, self.typesNumRows, self.typesNumCols)

    def testReaderComments(self):
        rows = []
        for row in TabFileReader(self.getInputFile("typesComment.tsv"), hashAreComments=True):
            rows.append(row)
        self.checkRowsCols(rows, self.typesNumRows-1, self.typesNumCols)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(TabFileTests))
    return ts

if __name__ == '__main__':
    unittest.main()
