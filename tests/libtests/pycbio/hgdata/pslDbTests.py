# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.psl import PslDbReader
from pycbio.hgdata.hgConf import HgConf
from socket import gethostname

# only run on these machines
testHosts = set(["hgwdev"])
testDb = "hg18"
testTbl = "refSeqAli"

onTestHost = gethostname() in testHosts
if not onTestHost:
    sys.stderr.write("Note: not running on test host, skipping PslDbTest\n")


class DbReadTests(TestCaseBase):
    """database read tests.  Only run on certain hosts"""

    hgConf = None  # load on first use

    def __connect(self):
        if self.hgConf is None:
            self.hgConf = HgConf()
        import MySQLdb
        return MySQLdb.connect(host=self.hgConf["db.host"], user=self.hgConf["db.user"], passwd=self.hgConf["db.password"], db=testDb)

    def testDbQueryLoad(self):
        conn = self.__connect()
        try:
            # just read 10 PSLs
            pslCnt = 0
            for psl in PslDbReader(conn, "select * from %s limit 10" % testTbl):
                pslCnt += 1
            self.assertEqual(pslCnt, 10)
        finally:
            conn.close()

    def testDbRangeLoad(self):
        conn = self.__connect()
        qNames = set()
        try:
            for psl in PslDbReader.targetRangeQuery(conn, testTbl, "chr22", 16650000, 20470000):
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
