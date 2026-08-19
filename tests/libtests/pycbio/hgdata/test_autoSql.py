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
