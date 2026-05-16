# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from collections import namedtuple
import pytest
from pycbio.tsv import TsvReader, TsvWriter, TsvError
from pycbio.tsv.tsvColumns import columnsSpecBuild
import pycbio.sys.testingSupport as ts


def _onOffParse(s):
    if s == "on":
        return True
    elif s == "off":
        return False
    else:
        raise ValueError("invalid onOff value: " + s)

def _onOffFmt(val):
    if val:
        return "on"
    else:
        return "off"


_columns = ["strCol", "intCol", "floatCol", "onOffCol"]
_typeMap = {"intCol": int, "floatCol": float, "onOffCol": (_onOffParse, _onOffFmt)}


def testWriteFromDicts(request):
    """write rows from dicts"""
    rows = [{"strCol": "name1", "intCol": 10, "floatCol": 10.01, "onOffCol": True},
            {"strCol": "name2", "intCol": 20, "floatCol": 20.22, "onOffCol": False},
            {"strCol": "name3", "intCol": 30, "floatCol": 30.555, "onOffCol": False}]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:

        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteFromLists(request):
    """write rows from lists"""
    rows = [["name1", 10, 10.01, True],
            ["name2", 20, 20.22, False],
            ["name3", 30, 30.555, False]]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:

        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteFromTsvRows(request):
    """read TSV rows and write them back out"""
    inFile = ts.get_test_input_file(request, "types.tsv")
    rows = [r for r in TsvReader(inFile, typeMap=_typeMap)]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:
        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteFromNamedtuples(request):
    """write rows from namedtuples"""
    Row = namedtuple("Row", _columns)
    rows = [Row("name1", 10, 10.01, True),
            Row("name2", 20, 20.22, False),
            Row("name3", 30, 30.555, False)]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:

        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteNoTypeMap(request):
    """write rows without type conversion"""
    rows = [["name1", "10", "10.01", "on"],
            ["name2", "20", "20.22", "off"],
            ["name3", "30", "30.555", "off"]]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns) as wr:

        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteToFh(request):
    """write using an existing file handle"""
    rows = [["name1", 10, 10.01, True],
            ["name2", 20, 20.22, False],
            ["name3", 30, 30.555, False]]
    outFile = ts.get_test_output_file(request, ".tsv")
    with open(outFile, "w") as fh:
        wr = TsvWriter(outFile, columns=_columns, typeMap=_typeMap, outFh=fh)

        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteNoneValues(request):
    """write rows containing None values"""
    rows = [{"strCol": "name1", "intCol": None, "floatCol": 10.01, "onOffCol": True},
            {"strCol": None, "intCol": 20, "floatCol": None, "onOffCol": False}]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:

        wr.writeRows(rows)
    ts.diff_results_expected(request, ".tsv")

def testWriteColumns(request):
    """write rows using keyword arguments, with some missing columns"""
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:

        wr.writeColumns(strCol="name1", intCol=10, floatCol=10.01, onOffCol=True)
        wr.writeColumns(strCol="name2", floatCol=20.22)
        wr.writeColumns(onOffCol=False)
    ts.diff_results_expected(request, ".tsv")

def testWriteGzip(request):
    """write to a gzip compressed file"""
    rows = [["name1", 10, 10.01, True],
            ["name2", 20, 20.22, False],
            ["name3", 30, 30.555, False]]
    outFile = ts.get_test_output_file(request, ".tsv.gz")
    with TsvWriter(outFile, columns=_columns, typeMap=_typeMap) as wr:

        wr.writeRows(rows)
    # read back and verify
    readRows = [r for r in TsvReader(outFile, typeMap=_typeMap)]
    assert len(readRows) == 3
    assert readRows[0].strCol == "name1"
    assert readRows[0].intCol == 10
    assert readRows[2].onOffCol is False


def testWriteFromColumnSpecs(request):
    """pre-built ColumnSpecs may be passed instead of columns/typeMap"""
    specs = columnsSpecBuild(_columns, _typeMap, None)
    rows = [["name1", 10, 10.01, True],
            ["name2", 20, 20.22, False]]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columnSpecs=specs) as wr:
        wr.writeRows(rows)
    readRows = [r for r in TsvReader(outFile, typeMap=_typeMap)]
    assert [r.strCol for r in readRows] == ["name1", "name2"]
    assert readRows[1].onOffCol is False


def testWriteColumnsDerivedFromTypeMap(request):
    """when typeMap is given but columns is not, columns come from typeMap keys"""
    typeMap = {"a": int, "b": float, "c": (str, str)}
    rows = [[1, 1.5, "x"], [2, 2.5, "y"]]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, typeMap=typeMap) as wr:
        assert wr.columns == ["a", "b", "c"]
        wr.writeRows(rows)
    readRows = [r for r in TsvReader(outFile, typeMap=typeMap)]
    assert [(r.a, r.b, r.c) for r in readRows] == [(1, 1.5, "x"), (2, 2.5, "y")]


def testWriteNoColumnsRejected():
    with pytest.raises(TsvError):
        TsvWriter("/tmp/never-used.tsv")


def testColumnSpecsConflict():
    specs = columnsSpecBuild(_columns, _typeMap, None)
    with pytest.raises(TsvError):
        TsvWriter("/tmp/never-used.tsv", columns=_columns, columnSpecs=specs)
