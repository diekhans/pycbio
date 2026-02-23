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

###
# rowClass tests
###
class TypeRow:
    """Row class for types.tsv"""
    def __init__(self, row):
        self.col0 = row[0]
        self.col1 = row[1]
        self.col2 = row[2]
        self.col3 = row[3]

def testTableRowClass(request):
    """Test TabFile with rowClass parameter"""
    tbl = TabFile(ts.get_test_input_file(request, "types.tsv"), rowClass=TypeRow)
    assert len(tbl) == typesNumRows
    for row in tbl:
        assert isinstance(row, TypeRow)
        assert hasattr(row, 'col0')
        assert hasattr(row, 'col1')

def testReaderRowClass(request):
    """Test TabFileReader with rowClass parameter"""
    rows = list(TabFileReader(ts.get_test_input_file(request, "types.tsv"), rowClass=TypeRow))
    assert len(rows) == typesNumRows
    for row in rows:
        assert isinstance(row, TypeRow)

###
# skipBlankLines tests
###
def testReaderSkipBlankLines(request):
    """Test TabFileReader with skipBlankLines parameter"""
    # Create a file with blank lines
    outf = ts.get_test_output_file(request, ".tsv")
    with open(outf, "w") as fh:
        fh.write("a\tb\tc\n")
        fh.write("\n")
        fh.write("d\te\tf\n")
        fh.write("\n")
    rows = list(TabFileReader(outf, skipBlankLines=True))
    assert len(rows) == 2
    assert rows[0] == ["a", "b", "c"]
    assert rows[1] == ["d", "e", "f"]

def testTableSkipBlankLines(request):
    """Test TabFile with skipBlankLines parameter"""
    outf = ts.get_test_output_file(request, ".tsv")
    with open(outf, "w") as fh:
        fh.write("a\tb\tc\n")
        fh.write("\n")
        fh.write("d\te\tf\n")
    tbl = TabFile(outf, skipBlankLines=True)
    assert len(tbl) == 2

###
# File handle tests
###
def testReaderFileHandle(request):
    """Test TabFileReader with file handle"""
    with open(ts.get_test_input_file(request, "types.tsv")) as fh:
        rows = list(TabFileReader(fh))
    assert len(rows) == typesNumRows

###
# Combined options tests
###
def testReaderAllOptions(request):
    """Test TabFileReader with multiple options combined"""
    outf = ts.get_test_output_file(request, ".tsv")
    with open(outf, "w") as fh:
        fh.write("# comment\n")
        fh.write("a\tb\tc\td\n")
        fh.write("\n")
        fh.write("1\t2\t3\t4\n")
    rows = list(TabFileReader(outf, rowClass=TypeRow, hashAreComments=True, skipBlankLines=True))
    assert len(rows) == 2
    assert isinstance(rows[0], TypeRow)
    assert rows[0].col0 == "a"
