# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.tsv import TabFile, TabFileReader
import pycbio.sys.testingSupport as ts
import pipettor

typesNumRows = 4
typesNumCols = 4

def checkRowsCols(rows, expectNumRows, expectNumCols):
    numRows = 0
    for row in rows:
        assert len(row) == expectNumCols
        numRows += 1


def testTable(request):
    tbl = TabFile(ts.get_test_input_file(request, "types.tsv"))
    checkRowsCols(tbl, typesNumRows, typesNumCols)

def testTableComments(request):
    tbl = TabFile(ts.get_test_input_file(request, "typesComment.tsv"), hashAreComments=True)
    checkRowsCols(tbl, typesNumRows - 1, typesNumCols)

def testReader(request):
    rows = []
    for row in TabFileReader(ts.get_test_input_file(request, "types.tsv")):
        rows.append(row)
    checkRowsCols(rows, typesNumRows, typesNumCols)

def testReaderGzip(request):
    tsvGz = ts.get_test_output_file(request, "tsv.gz")
    pipettor.run(["gzip", "-c", ts.get_test_input_file(request, "types.tsv")], stdout=tsvGz)
    rows = [row for row in TabFileReader(tsvGz)]
    checkRowsCols(rows, typesNumRows, typesNumCols)

def testReaderComments(request):
    rows = [row for row in TabFileReader(ts.get_test_input_file(request, "typesComment.tsv"), hashAreComments=True)]
    checkRowsCols(rows, typesNumRows - 1, typesNumCols)
