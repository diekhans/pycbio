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

def testFloatArraySplit():
    assert autoSql.floatArraySplit("1.5,2.5,") == [1.5, 2.5]
    assert autoSql.floatArraySplit("") == []

def testFloatArraySplitNotANumber():
    "the same reporting intArraySplit gives, rather than a bare float() failure"
    with pytest.raises(PycbioDataError, match=r"not a comma-separated list of numbers: '1.5,fred,'"):
        autoSql.floatArraySplit("1.5,fred,")
