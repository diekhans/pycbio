# Copyright 2006-2025 Mark Diekhans
import sys
import os.path as osp
import pytest

sys.path = ["../../../../lib", "../.."] + sys.path
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.chromInfo import ChromInfoTbl
from testlib.mysqlCheck import mysqlTestsEnvAvailable, skip_if_no_mysql

if mysqlTestsEnvAvailable():
    from pycbio.hgdata.hgDb import connect

expect10Chroms = (("chr1", 248956422),
                  ("chr2", 242193529),
                  ("chr3", 198295559),
                  ("chr4", 190214555),
                  ("chr5", 181538259),
                  ("chr6", 170805979),
                  ("chr7", 159345973),
                  ("chrX", 156040895),
                  ("chr8", 145138636),
                  ("chr9", 138394717))

def _checkChroms(chroms):
    got10Chroms = tuple([(c.chrom, c.size)
                         for c in sorted(chroms.values(), key=lambda c: c.size, reverse=True)[0:10]])
    assert got10Chroms == expect10Chroms

def testLoadFile(request):
    chroms = ChromInfoTbl.loadFile(ts.get_test_input_file(request, "chrom.sizes"))
    _checkChroms(chroms)

@skip_if_no_mysql()
def testLoadDb():
    hgdb = "hg38"
    with connect(hgdb) as conn:
        chroms = ChromInfoTbl.loadDb(conn)
        _checkChroms(chroms)

def testLoadTwoBit():
    hg38TwoBit = "/hive/data/genomes/hg38/hg38.2bit"
    if not osp.exists(hg38TwoBit):
        pytest.skip(f"hg38 genome twoBit not found: {hg38TwoBit}")
    else:
        chroms = ChromInfoTbl.loadTwoBit(hg38TwoBit)
        _checkChroms(chroms)
