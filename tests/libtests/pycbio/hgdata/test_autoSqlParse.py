# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

import pytest
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.autoSqlParse import (parseAutoSql, parseAutoSqlText,
                                        AutoSqlParseError, AsType)


def testBed3(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "bed.as"))
    assert len(objs) == 1
    t = objs[0]
    assert t.declType == "table"
    assert t.name == "bed"
    assert t.comment == "Browser extensible data"
    assert tuple(f.name for f in t.fields) == ("chrom", "chromStart", "chromEnd", "name")
    assert t.fields[0].type == AsType(name="string")
    assert t.fields[1].type == AsType(name="uint")


def testBed6(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "bed6.as"))
    t = objs[0]
    assert tuple(f.name for f in t.fields) == ("chrom", "chromStart", "chromEnd", "name", "score", "strand")
    strand = t.fields[5]
    assert strand.type.name == "char"
    assert strand.type.isArray and strand.type.arraySize == 1


def testBed12VarArrays(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "bed12Source.as"))
    t = objs[0]
    fieldsByName = {f.name: f for f in t.fields}
    sz = fieldsByName["blockSizes"]
    assert sz.type.name == "int"
    assert sz.type.isArray
    assert sz.type.arraySize == "blockCount"
    assert fieldsByName["source"].type == AsType(name="string")


def testBed8AttrsVarArrays(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "bed8Attrs.as"))
    t = objs[0]
    names = [f.name for f in t.fields]
    assert names[-3:] == ["attrCount", "attrTags", "attrVals"]
    tags = t.fields[-2]
    assert tags.type.name == "string"
    assert tags.type.isArray and tags.type.arraySize == "attrCount"


def testBarChartBedFloatArray(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "barChartBed.as"))
    t = objs[0]
    f = next(f for f in t.fields if f.name == "expScores")
    assert f.type.name == "float"
    assert f.type.isArray and f.type.arraySize == "expCount"
    f2 = next(f for f in t.fields if f.name == "_dataOffset")
    assert f2.type == AsType(name="bigint")


def testBedMethylNoArrays(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "bedMethyl.as"))
    t = objs[0]
    extras = [f for f in t.fields[9:]]
    assert len(extras) == 9
    assert all(f.type.name == "string" and not f.type.isArray for f in extras)


def testEnumAndSet(request):
    objs = parseAutoSql(ts.get_test_input_file(request, "doc.as"))
    assert len(objs) == 2
    addr, symbolCols = objs
    assert addr.name == "addressBook"
    # primary/index/auto handling
    name = addr.fields[0]
    assert name.indexType == "primary"
    assert not name.auto
    city = next(f for f in addr.fields if f.name == "city")
    assert city.indexType == "index"
    assert city.indexSize == 6
    assert symbolCols.name == "symbolCols"
    id_ = symbolCols.fields[0]
    assert id_.indexType == "primary" and id_.auto
    sex = symbolCols.fields[1]
    assert sex.type.name == "enum"
    assert sex.type.enumValues == ("male", "female")
    skills = symbolCols.fields[2]
    assert skills.type.name == "set"
    assert skills.type.enumValues == ("cProg", "javaProg", "pythonProg", "awkProg")


def testNestedSimpleRejected():
    src = '''table foo "x" (
        int n; "count"
        simple point pts; "nested"
    )
    '''
    with pytest.raises(AutoSqlParseError):
        parseAutoSqlText(src)


def testTokenError():
    with pytest.raises(AutoSqlParseError):
        parseAutoSqlText('table foo "x" ( int x !! "bad"; )')
