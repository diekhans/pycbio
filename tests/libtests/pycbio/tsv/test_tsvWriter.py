# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from collections import namedtuple
import pytest
from pycbio.tsv import TsvReader, TsvWriter, TsvError
from pycbio.tsv.tsvRow import tsvRowGetColumnSpecs
from pycbio.tsv.tsvColumns import ColumnSpecs, columnsSpecBuild
from pycbio.sys.symEnum import SymEnum, SymEnumValue
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


def testCopyTsvViaReaderSpecs(request):
    """read a TSV, take ColumnSpecs from the reader, write a copy through TsvWriter,
    and verify byte-for-byte identity with the input."""
    inFile = ts.get_test_input_file(request, "types.tsv")
    reader = TsvReader(inFile, typeMap=_typeMap)
    specs = reader.columnSpecs
    assert isinstance(specs, ColumnSpecs)
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columnSpecs=specs) as wr:
        for row in reader:
            wr.writeRow(row)
    with open(inFile) as fh:
        expected = fh.read()
    with open(outFile) as fh:
        actual = fh.read()
    assert actual == expected


class _Color(SymEnum):
    purple = 1
    gold = 2
    black = 3


class _Feature(SymEnum):
    """SymEnum with external names containing non-identifier chars"""
    promoter = 1
    utr5 = SymEnumValue(2, "5'UTR")
    cds = SymEnumValue(3, "CDS")


def testWriteSymEnumColumn(request):
    """A SymEnum subclass placed as a scalar type in typeMap should parse via
    SymEnum(str) on read and format via str(member) on write, round-tripping
    the textual values."""
    typeMap = {"name": str, "color": _Color, "feature": _Feature}
    rows = [
        {"name": "tx1", "color": _Color.purple, "feature": _Feature.promoter},
        {"name": "tx2", "color": _Color.gold, "feature": _Feature.utr5},
        {"name": "tx3", "color": _Color.black, "feature": _Feature.cds},
    ]
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columns=["name", "color", "feature"], typeMap=typeMap) as wr:
        wr.writeRows(rows)
    with open(outFile) as fh:
        content = fh.read()
    assert content == ("name\tcolor\tfeature\n"
                       "tx1\tpurple\tpromoter\n"
                       "tx2\tgold\t5'UTR\n"
                       "tx3\tblack\tCDS\n")
    # parsed back as SymEnum members
    readRows = list(TsvReader(outFile, typeMap=typeMap))
    assert readRows[0].color is _Color.purple
    assert readRows[1].feature is _Feature.utr5
    assert readRows[2].feature is _Feature.cds


def testCopyTsvViaRowSpecs(request):
    """get ColumnSpecs from a TsvRow via tsvRowGetColumnSpecs() and use it to
    write a copy of the TSV."""
    inFile = ts.get_test_input_file(request, "types.tsv")
    rows = list(TsvReader(inFile, typeMap=_typeMap))
    assert len(rows) > 0
    specs = tsvRowGetColumnSpecs(rows[0])
    assert isinstance(specs, ColumnSpecs)
    # same specs object as the reader holds
    assert specs is tsvRowGetColumnSpecs(rows[-1])
    outFile = ts.get_test_output_file(request, ".tsv")
    with TsvWriter(outFile, columnSpecs=specs) as wr:
        wr.writeRows(rows)
    with open(inFile) as fh:
        expected = fh.read()
    with open(outFile) as fh:
        actual = fh.read()
    assert actual == expected
