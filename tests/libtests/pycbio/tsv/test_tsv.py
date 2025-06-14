# Copyright 2006-2025 Mark Diekhans
# -*- coding: utf-8 -*-
import unittest
import sys
import math
from csv import excel_tab, excel
import pickle
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from collections import namedtuple
from pycbio.tsv import TsvReader, tsvRowToDict, printf_basic_dialect
from pycbio.sys.testCaseBase import TestCaseBase
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


class ReadTests(TestCaseBase):
    def testLoad(self):
        rows = [r for r in TsvReader(self.getInputFile("mrna1.tsv"))]
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertEqual(len(r), 22)
        r = rows[0]
        self.assertEqual(r["qName"], "BC032353")
        self.assertEqual(r[10], "BC032353")
        self.assertEqual(r.qName, "BC032353")

        self.assertEqual(r.get(10), "BC032353")
        self.assertEqual(r.get("qName"), "BC032353")

        self.assertEqual(r.get(1000, "pastend"), "pastend")
        self.assertEqual(r.get("fName", "fred"), "fred")

        d = tsvRowToDict(r)
        self.assertEqual(d["qName"], "BC032353")

    def _doReadColTypes(self, inFile):
        typeMap = {"intCol": int, "floatCol": float, "onOffCol": (_onOffParse, _onOffFmt)}
        return [r for r in TsvReader(self.getInputFile(inFile), typeMap=typeMap)]

    def _doCheckColTypes(self, rows):
        r = rows[0]
        self.assertEqual(r.strCol, "name1")
        self.assertEqual(r.intCol, 10)
        self.assertEqual(r.floatCol, 10.01)
        self.assertEqual(str(r), "name1\t10\t10.01\ton")

        r = rows[2]
        self.assertEqual(r.strCol, "name3")
        self.assertEqual(r.intCol, 30)
        self.assertEqual(r.floatCol, 30.555)
        self.assertEqual(str(r), "name3\t30\t30.555\toff")

    def _doTestColType(self, inFile):
        rows = self._doReadColTypes(inFile)
        self._doCheckColTypes(rows)

    def testColType(self):
        self._doTestColType("types.tsv")

    def testColCommentType(self):
        self._doTestColType("typesComment.tsv")

    def testColTypePickle(self):
        rows = self._doReadColTypes("types.tsv")
        rowsp = pickle.loads(pickle.dumps(rows))
        self._doCheckColTypes(rowsp)

    def testColTypeDefault(self):
        # default to int type
        typeMap = {"strand": str, "qName": str, "tName": str,
                   "blockSizes": intArrayType,
                   "qStarts": intArrayType, "tStarts": intArrayType}

        rowTbl = {r.qName: r for r in TsvReader(self.getInputFile("mrna1.tsv"),
                                                typeMap=typeMap, defaultColType=int)}
        r = rowTbl["AK095183"]
        self.assertEqual(r.tStart, 4222)
        self.assertEqual(r.tEnd, 19206)
        self.assertEqual(r.tName, "chr1")
        self.assertEqual(r.tStart, 4222)

        tStarts = (4222, 4832, 5658, 5766, 6469, 6719, 7095, 7355, 7777, 8130, 14600, 19183)
        self.assertEqual(len(r.tStarts), len(tStarts))
        for i in range(len(tStarts)):
            self.assertEqual(r.tStarts[i], tStarts[i])

    def testColNameMap(self):
        typeMap = {"int_col": int, "float_col": float, "onOff_col": (_onOffParse, _onOffFmt)}

        rows = [r for r in TsvReader(self.getInputFile('typesColNameMap.tsv'), typeMap=typeMap,
                                     columnNameMapper=lambda s: s.replace(' ', '_'))]
        specs = rows[0]._columnSpecs_
        self.assertEqual(specs.columns, ['str_col', 'int_col', 'float_col', 'onOff_col'])
        self.assertEqual(specs.extColumns, ['str col', 'int col', 'float col', 'onOff col'])

        r = rows[0]
        self.assertEqual(r.str_col, "name1")
        self.assertEqual(r.int_col, 10)
        self.assertEqual(r.float_col, 10.01)
        self.assertEqual(str(r), "name1\t10\t10.01\ton")

        r = rows[2]
        self.assertEqual(r.str_col, "name3")
        self.assertEqual(r.int_col, 30)
        self.assertEqual(r.float_col, 30.555)
        self.assertEqual(str(r), "name3\t30\t30.555\toff")

    def testColNameMapNoRowClass(self):
        # check column conversion without a rowClass
        typeMap = {"intCol": int, "floatCol": float, "onOffCol": (_onOffParse, _onOffFmt)}
        tsvReader = TsvReader(self.getInputFile('typesNan.tsv'), typeMap=typeMap, rowClass=(lambda rdr, row: row))
        rows = [r for r in tsvReader]
        r = rows[1]
        # will get ['name2', 20, math.nan, False], but nan != an
        self.assertEqual(r[0:2], ['name2', 20])
        self.assertTrue(math.isnan(r[2]))
        self.assertEqual(r[3], False)

        self.assertEqual(tsvReader.formatRow(r), ['name2', '20', 'nan', 'off'])

    def testWrite(self):
        rows = [r for r in TsvReader(self.getInputFile("mrna1.tsv"))]
        with open(self.getOutputFile(".tsv"), "w") as fh:
            rows[0].writeHeader(fh)
            for r in rows:
                r.write(fh)
        self.diffExpected(".tsv")

    def readMRna1(self, inFile):
        "verify TsvReader on a mrna1.tsv derived file"
        rowCnt = 0
        for row in TsvReader(inFile):
            self.assertEqual(len(row), 22)
            rowCnt += 1
        self.assertEqual(rowCnt, 10)

    def testReader(self):
        self.readMRna1(self.getInputFile("mrna1.tsv"))

    def testReadGzip(self):
        tsvGz = self.getOutputFile("tsv.gz")
        pipettor.run(["gzip", "-c", self.getInputFile("mrna1.tsv")], stdout=tsvGz)
        self.readMRna1(tsvGz)

    def testReadBzip2(self):
        tsvBz = self.getOutputFile("tsv.bz2")
        pipettor.run(["bzip2", "-c", self.getInputFile("mrna1.tsv")], stdout=tsvBz)
        self.readMRna1(tsvBz)

    def testAllowEmptyReader(self):
        cnt = 0
        for row in TsvReader("/dev/null", allowEmpty=True):
            cnt += 1
        self.assertEqual(cnt, 0)

    def testPrintfed(self):
        # created with escaped quotes in data
        rows = [r for r in TsvReader(self.getInputFile("printfed-with-quotes.tsv"), dialect=printf_basic_dialect)]
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[1].Mentions, '"GP I')

    def testHashSpace(self):
        # headers like UCSC chromAlias "# ucsc	assembly"
        rdr = TsvReader(self.getInputFile("GCF_003709585.1.chromAlias.tsv"))
        rows = [r for r in rdr]
        self.assertEqual(rdr.columns, ["ucsc", "assembly", "custom", "genbank", "ncbi", "refseq"])
        self.assertEqual(rows[0].ucsc, 'NW_020834726v1')

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

    def _weirdCaseTester(self, infile, dialect):
        rows = [r for r in TsvReader(self.getInputFile(infile), dialect=dialect,
                                     encoding="utf-8", typeMap={"num_col": int})]
        self.assertEqual(len(self._weirdExpectExcel), len(rows))
        for exp, row in zip(self._weirdExpectExcel, rows):
            self.assertEqual(exp.num_col, row.num_col)
            self.assertEqual(exp.text_col, row.text_col)
            self.assertEqual(exp.another, row.another)

    def testWeirdCharsDosCsv(self):
        self._weirdCaseTester("weird-chars.dos.csv", excel)

    def testWeirdCharsDosTab(self):
        self._weirdCaseTester("weird-chars.dos.tab", excel_tab)

    def testWeirdCharsMacCsv(self):
        self._weirdCaseTester("weird-chars.mac.csv", excel)

    def testWeirdCharsMacTab(self):
        self._weirdCaseTester("weird-chars.mac.tab", excel_tab)

    def testWeirdCharsUnixCsv(self):
        self._weirdCaseTester("weird-chars.unix.csv", excel)

    def testWeirdCharsUnixTab(self):
        self._weirdCaseTester("weird-chars.unix.tab", excel_tab)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ReadTests))
    return ts


if __name__ == '__main__':
    unittest.main()
