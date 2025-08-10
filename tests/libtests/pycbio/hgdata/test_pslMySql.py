# Copyright 2006-2025 Mark Diekhans
import sys
import pytest
sys.path = ["../../../../lib", "../.."] + sys.path
from pycbio.hgdata.hgConf import HgConf
from testlib.mysqlCheck import mysqlTestsEnvAvailable, skip_if_no_mysql

if mysqlTestsEnvAvailable():
    from pycbio.hgdata import hgDb
    from pycbio.hgdata.pslMySqlReader import PslMySqlReader

# only run on these machines
testDb = "hg18"
testTbl = "refSeqAli"

def _connect():
    hgConf = HgConf()
    return hgDb.connect(db=testDb, hgConf=hgConf)

@skip_if_no_mysql()
def testDbQueryLoad(self):
    conn = self._connect()
    try:
        # just read 10 PSLs
        pslCnt = 0
        for psl in PslMySqlReader(conn, "select * from %s limit 10" % testTbl):
            pslCnt += 1
        assert pslCnt == 10
    finally:
        conn.close()

@skip_if_no_mysql()
def testDbRangeLoad(self):
    conn = self._connect()
    qNames = set()
    try:
        for psl in PslMySqlReader.targetRangeQuery(conn, testTbl, "chr22", 16650000, 20470000):
            assert psl.tName == "chr22"
            qNames.add(psl.qName)
    finally:
        conn.close()
    # Test a few identifiers are included.  Must change if removed from RefSeq
    for qName in ('NM_001178010', 'NM_001178011', 'NM_003325', 'NM_001009939'):
        if qName not in qNames:
            pytest.fail("qName not in refSeqAli select, maybe have to update test if RefSeq changed: " + qName)
