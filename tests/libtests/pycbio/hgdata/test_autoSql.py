# Copyright 2006-2026 Mark Diekhans
import sys
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio import PycbioDataError
from pycbio.hgdata import autoSql

def testStrArraySplit():
    assert autoSql.strArraySplit("a,b,c,") == ["a", "b", "c"]
    assert autoSql.strArraySplit("a,b,c") == ["a", "b", "c"]
    assert autoSql.strArraySplit("") == []

def testStrArraySplitAutoSqlCases():
    """the cases kent sqlStringDynamicArray produces: a trailing comma terminates,
    an empty element is an empty string, so a lone ',' is one empty string"""
    assert autoSql.strArraySplit(",") == [""]
    assert autoSql.strArraySplit(",,") == ["", ""]
    assert autoSql.strArraySplit("a,,c,") == ["a", "", "c"]
    assert autoSql.strArraySplit(",b,") == ["", "b"]
    assert autoSql.strArraySplit("a,,") == ["a", ""]

def testStrArraySplitNone():
    "the same cases with an empty element taken as a missing value"
    assert autoSql.strArraySplitNone("") == []
    assert autoSql.strArraySplitNone(",") == [None]
    assert autoSql.strArraySplitNone("a,b,c,") == ["a", "b", "c"]
    assert autoSql.strArraySplitNone("ENSG00000125991.19,,") == ["ENSG00000125991.19", None]
    assert autoSql.strArraySplitNone(",b,") == [None, "b"]

def testStrArraySplitNoneRoundTrip():
    for strs in ([], ["a"], ["a", None], [None, "b", None]):
        assert autoSql.strArraySplitNone(autoSql.strArrayJoin(strs)) == strs

def testStrArraySplitBytes():
    "autoSql columns are longblob, so a value from mysql arrives as bytes"
    assert autoSql.strArraySplit(b"a,b,c,") == ["a", "b", "c"]

def testIntArraySplit():
    assert autoSql.intArraySplit("50,60,") == [50, 60]
    assert autoSql.intArraySplit("50,60") == [50, 60]
    assert autoSql.intArraySplit("") == []

def testIntArraySplitEmptyField():
    """an empty field used to surface as a bare int() ValueError, which said
    nothing about the list it came from"""
    with pytest.raises(PycbioDataError,
                       match=r"not a comma-separated list of integers: '50,,50,'"):
        autoSql.intArraySplit("50,,50,")

def testIntArraySplitNotANumber():
    with pytest.raises(PycbioDataError, match="not a comma-separated list of integers"):
        autoSql.intArraySplit("50,fred,")

def testIntArrayJoinRoundTrip():
    assert autoSql.intArraySplit(autoSql.intArrayJoin([50, 60])) == [50, 60]

###
# a missing element is an empty element, never the string "None", which would land
# in the data file: FLAIR hit exactly that in a BED extra column
###
def testStrArrayJoinNone():
    assert autoSql.strArrayJoin(["ENSG00000125991.19", None]) == "ENSG00000125991.19,,"
    assert autoSql.strArrayJoin([None]) == ","
    assert autoSql.strArrayJoin([None, "b", None]) == ",b,,"

def testIntArrayJoinNone():
    assert autoSql.intArrayJoin([1, None, 3]) == "1,,3,"

def testFloatArrayJoinNone():
    assert autoSql.floatArrayJoin([1.5, None]) == "1.5,,"
    assert autoSql.floatArrayJoin([1.5, None], fmt="{:.2f}") == "1.50,,"

def testJoinEmptyAndNone():
    for join in (autoSql.strArrayJoin, autoSql.intArrayJoin, autoSql.floatArrayJoin):
        assert join(None) == ""
        assert join([]) == ""

def testIntArraySplitNone():
    "an empty element is a missing value rather than the error intArraySplit gives"
    assert autoSql.intArraySplitNone("") == []
    assert autoSql.intArraySplitNone("50,60,") == [50, 60]
    assert autoSql.intArraySplitNone("50,,50,") == [50, None, 50]
    assert autoSql.intArraySplitNone(",") == [None]

def testIntArraySplitNoneNotANumber():
    with pytest.raises(PycbioDataError, match="not a comma-separated list of integers"):
        autoSql.intArraySplitNone("50,fred,")

def testFloatArraySplitNone():
    assert autoSql.floatArraySplitNone("") == []
    assert autoSql.floatArraySplitNone("1.5,,2.5,") == [1.5, None, 2.5]
    assert autoSql.floatArraySplitNone(",") == [None]

def testFloatArraySplitNoneNotANumber():
    with pytest.raises(PycbioDataError, match="not a comma-separated list of numbers"):
        autoSql.floatArraySplitNone("1.5,fred,")

def testArraySplitNoneRoundTrip():
    for split, join, values in ((autoSql.strArraySplitNone, autoSql.strArrayJoin, ["a", None, "c"]),
                                (autoSql.intArraySplitNone, autoSql.intArrayJoin, [1, None, 3]),
                                (autoSql.floatArraySplitNone, autoSql.floatArrayJoin, [1.5, None, 3.5])):
        assert split(join(values)) == values
        assert split(join([])) == []
        assert split(join(None)) == []

def testFloatArraySplit():
    assert autoSql.floatArraySplit("1.5,2.5,") == [1.5, 2.5]
    assert autoSql.floatArraySplit("") == []

def testFloatArraySplitNotANumber():
    "the same reporting intArraySplit gives, rather than a bare float() failure"
    with pytest.raises(PycbioDataError, match=r"not a comma-separated list of numbers: '1.5,fred,'"):
        autoSql.floatArraySplit("1.5,fred,")
