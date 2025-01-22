# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.tsv import TabFile, TabFileReader
from pycbio.sys.testCaseBase import TestCaseBase
import pipettor


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
        self.checkRowsCols(tbl, self.typesNumRows - 1, self.typesNumCols)

    def testReader(self):
        rows = []
        for row in TabFileReader(self.getInputFile("types.tsv")):
            rows.append(row)
        self.checkRowsCols(rows, self.typesNumRows, self.typesNumCols)

    def testReaderGzip(self):
        tsvGz = self.getOutputFile("tsv.gz")
        pipettor.run(["gzip", "-c", self.getInputFile("types.tsv")], stdout=tsvGz)
        rows = [row for row in TabFileReader(tsvGz)]
        self.checkRowsCols(rows, self.typesNumRows, self.typesNumCols)

    def testReaderComments(self):
        rows = [row for row in TabFileReader(self.getInputFile("typesComment.tsv"), hashAreComments=True)]
        self.checkRowsCols(rows, self.typesNumRows - 1, self.typesNumCols)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(TabFileTests))
    return ts


if __name__ == '__main__':
    unittest.main()
