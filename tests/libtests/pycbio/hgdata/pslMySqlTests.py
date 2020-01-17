# Copyright 2006-2012 Mark Diekhans
from __future__ import print_function
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.pslMySqlReader import PslMySqlReader
from pycbio.hgdata.hgConf import HgConf
from pycbio.hgdata import hgDb
from socket import gethostname

# only run on these machines
testHosts = set(["hgwdev"])
testDb = "hg18"
testTbl = "refSeqAli"

onTestHost = gethostname() in testHosts
if not onTestHost:
    sys.stderr.write("Note: not running on test host, skipping PslMySqlTest\n")


class DbReadTests(TestCaseBase):
    """database read tests.  Only run on certain hosts"""

    hgConf = None  # load on first use

    def _connect(self):
        if self.hgConf is None:
            self.hgConf = HgConf()
        return hgDb.connect(db=testDb, hgConf=self.hgConf)

    def testDbQueryLoad(self):
        conn = self._connect()
        try:
            # just read 10 PSLs
            pslCnt = 0
            for psl in PslMySqlReader(conn, "select * from %s limit 10" % testTbl):
                pslCnt += 1
            self.assertEqual(pslCnt, 10)
        finally:
            conn.close()

    def testDbRangeLoad(self):
        conn = self._connect()
        qNames = set()
        try:
            for psl in PslMySqlReader.targetRangeQuery(conn, testTbl, "chr22", 16650000, 20470000):
                self.assertEqual(psl.tName, "chr22")
                qNames.add(psl.qName)
        finally:
            conn.close()
        # Test a few identifiers are included.  Must change if removed from RefSeq
        for qName in ('NM_001178010', 'NM_001178011', 'NM_003325', 'NM_001009939'):
            if qName not in qNames:
                self.fail("qName not in refSeqAli select, maybe have to update test if RefSeq changed: " + qName)


def suite():
    ts = unittest.TestSuite()
    if onTestHost:
        ts.addTest(unittest.makeSuite(DbReadTests))
    return ts


if __name__ == '__main__' and onTestHost:
    unittest.main()
