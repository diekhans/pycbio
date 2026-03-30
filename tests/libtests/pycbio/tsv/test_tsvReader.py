# Copyright 2006-2025 Mark Diekhans
# -*- coding: utf-8 -*-
import sys
import math
from csv import excel_tab, excel
import pickle
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from collections import namedtuple
from pycbio.tsv import TsvReader, tsvRowToDict, printf_basic_dialect
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.autoSql import intArrayType

def _onOffParse(str):
    if str == "on":
        return True
    elif str == "off":
        return False
    else:
        raise ValueError("invalid onOff value: " + str)

def _onOffFmt(val):
    if type(val) is not bool:
        raise TypeError("onOff value not a bool: " + str(type(val)))
    if val:
        return "on"
    else:
        return "off"

def testLoad(request):
    rows = [r for r in TsvReader(ts.get_test_input_file(request, "mrna1.tsv"))]
    assert len(rows) == 10
    for r in rows:
        assert len(r) == 22
    r = rows[0]
    assert r["qName"] == "BC032353"
    assert r[10] == "BC032353"
    assert r.qName == "BC032353"

    assert r.get(10) == "BC032353"
    assert r.get("qName") == "BC032353"

    assert r.get(1000, "pastend") == "pastend"
    assert r.get("fName", "fred") == "fred"

    d = tsvRowToDict(r)
    assert d["qName"] == "BC032353"

def _doReadColTypes(request, inFile):
    typeMap = {"intCol": int, "floatCol": float, "onOffCol": (_onOffParse, _onOffFmt)}
    return [r for r in TsvReader(ts.get_test_input_file(request, inFile), typeMap=typeMap)]

def _doCheckColTypes(rows):
    r = rows[0]
    assert r.strCol == "name1"
    assert r.intCol == 10
    assert r.floatCol == 10.01
    assert str(r) == "name1\t10\t10.01\ton"

    r = rows[2]
    assert r.strCol == "name3"
    assert r.intCol == 30
    assert r.floatCol == 30.555
    assert str(r) == "name3\t30\t30.555\toff"

def _doTestColType(request, inFile):
    rows = _doReadColTypes(request, inFile)
    _doCheckColTypes(rows)

def testColType(request):
    _doTestColType(request, "types.tsv")

def testColCommentType(request):
    _doTestColType(request, "typesComment.tsv")

def testColTypePickle(request):
    rows = _doReadColTypes(request, "types.tsv")
    rowsp = pickle.loads(pickle.dumps(rows))
    _doCheckColTypes(rowsp)

def testColTypeDefault(request):
    # default to int type
    typeMap = {"strand": str, "qName": str, "tName": str,
               "blockSizes": intArrayType,
               "qStarts": intArrayType, "tStarts": intArrayType}

    rowTbl = {r.qName: r for r in TsvReader(ts.get_test_input_file(request, "mrna1.tsv"),
                                            typeMap=typeMap, defaultColType=int)}
    r = rowTbl["AK095183"]
    assert r.tStart == 4222
    assert r.tEnd == 19206
    assert r.tName == "chr1"
    assert r.tStart == 4222

    tStarts = (4222, 4832, 5658, 5766, 6469, 6719, 7095, 7355, 7777, 8130, 14600, 19183)
    assert len(r.tStarts) == len(tStarts)
    for i in range(len(tStarts)):
        assert r.tStarts[i] == tStarts[i]

def testColNameMap(request):
    typeMap = {"int_col": int, "float_col": float, "onOff_col": (_onOffParse, _onOffFmt)}

    rows = [r for r in TsvReader(ts.get_test_input_file(request, 'typesColNameMap.tsv'), typeMap=typeMap,
                                 columnNameMapper=lambda s: s.replace(' ', '_'))]
    specs = rows[0]._columnSpecs_
    assert specs.columns == ['str_col', 'int_col', 'float_col', 'onOff_col']
    assert specs.extColumns == ['str col', 'int col', 'float col', 'onOff col']

    r = rows[0]
    assert r.str_col == "name1"
    assert r.int_col == 10
    assert r.float_col == 10.01
    assert str(r) == "name1\t10\t10.01\ton"

    r = rows[2]
    assert r.str_col == "name3"
    assert r.int_col == 30
    assert r.float_col == 30.555
    assert str(r) == "name3\t30\t30.555\toff"

def testColNameMapNoRowClass(request):
    # check column conversion without a rowClass
    typeMap = {"intCol": int, "floatCol": float, "onOffCol": (_onOffParse, _onOffFmt)}
    tsvReader = TsvReader(ts.get_test_input_file(request, 'typesNan.tsv'), typeMap=typeMap, rowClass=(lambda rdr, row: row))
    rows = [r for r in tsvReader]
    r = rows[1]
    # will get ['name2', 20, math.nan, False], but nan != an
    assert r[0:2] == ['name2', 20]
    assert math.isnan(r[2])
    assert r[3] is False

    assert tsvReader.formatRow(r) == ['name2', '20', 'nan', 'off']

def testWrite(request):
    rows = [r for r in TsvReader(ts.get_test_input_file(request, "mrna1.tsv"))]
    with open(ts.get_test_output_file(request, ".tsv"), "w") as fh:
        rows[0].writeHeader(fh)
        for r in rows:
            r.write(fh)
    ts.diff_results_expected(request, ".tsv")

def readMRna1(inFile):
    "verify TsvReader on a mrna1.tsv derived file"
    rowCnt = 0
    for row in TsvReader(inFile):
        assert len(row) == 22
        rowCnt += 1
    assert rowCnt == 10

def testReader(request):
    readMRna1(ts.get_test_input_file(request, "mrna1.tsv"))

def testReadGzip(request):
    tsvGz = ts.get_test_output_file(request, "tsv.gz")
    pipettor.run(["gzip", "-c", ts.get_test_input_file(request, "mrna1.tsv")], stdout=tsvGz)
    readMRna1(tsvGz)

def testReadBzip2(request):
    tsvBz = ts.get_test_output_file(request, "tsv.bz2")
    pipettor.run(["bzip2", "-c", ts.get_test_input_file(request, "mrna1.tsv")], stdout=tsvBz)
    readMRna1(tsvBz)

def testAllowEmptyReader(request):
    cnt = 0
    for row in TsvReader("/dev/null", allowEmpty=True):
        cnt += 1
    assert cnt == 0

def testPrintfed(request):
    # created with escaped quotes in data
    rows = [r for r in TsvReader(ts.get_test_input_file(request, "printfed-with-quotes.tsv"), dialect=printf_basic_dialect)]
    assert len(rows) == 5
    assert rows[1].Mentions == '"GP I'

def testHashSpace(request):
    # headers like UCSC chromAlias "# ucsc	assembly"
    rdr = TsvReader(ts.get_test_input_file(request, "GCF_003709585.1.chromAlias.tsv"))
    rows = [r for r in rdr]
    assert rdr.columns == ["ucsc", "assembly", "custom", "genbank", "ncbi", "refseq"]
    assert rows[0].ucsc == 'NW_020834726v1'

class WeirdCaseExpect(namedtuple("WeirdCaseExpect",
                                 ("num_col", "text_col", "another"))):
    __slots__ = ()


# N.B. printf_basic_dialect will not work on this as they contain embedded tables
_weirdExpectExcel = (
    WeirdCaseExpect(0, 'ab"cd', 'doublequote'),
    WeirdCaseExpect(1, "zaf'doh", 'singlequote'),
    WeirdCaseExpect(2, 'tab\there', 'tab_in_string'),
    WeirdCaseExpect(3, '£©½', 'utf8'),
)

def _weirdCaseTester(request, infile, dialect):
    rows = [r for r in TsvReader(ts.get_test_input_file(request, infile), dialect=dialect,
                                 encoding="utf-8", typeMap={"num_col": int})]
    assert len(_weirdExpectExcel) == len(rows)
    for exp, row in zip(_weirdExpectExcel, rows):
        assert exp.num_col == row.num_col
        assert exp.text_col == row.text_col
        assert exp.another == row.another

def testWeirdCharsDosCsv(request):
    _weirdCaseTester(request, "weird-chars.dos.csv", excel)

def testWeirdCharsDosTab(request):
    _weirdCaseTester(request, "weird-chars.dos.tab", excel_tab)

def testWeirdCharsMacCsv(request):
    _weirdCaseTester(request, "weird-chars.mac.csv", excel)

def testWeirdCharsMacTab(request):
    _weirdCaseTester(request, "weird-chars.mac.tab", excel_tab)

def testWeirdCharsUnixCsv(request):
    _weirdCaseTester(request, "weird-chars.unix.csv", excel)

def testWeirdCharsUnixTab(request):
    _weirdCaseTester(request, "weird-chars.unix.tab", excel_tab)
