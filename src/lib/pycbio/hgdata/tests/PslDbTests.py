# Copyright 2006-2011 Mark Diekhans
import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.hgdata.Psl import PslDbReader
from pycbio.hgdata.HgConf import HgConf
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
        if self.hgConf == None:
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
            self.failUnlessEqual(pslCnt, 10)
        finally:
            conn.close()

    def testDbRangeLoad(self):
        conn = self.__connect()
        try:
            psls = list(PslDbReader.targetRangeQuery(conn, testTbl, "chr22", 123, 456, useBin=True))
        finally:
            conn.close()

def suite():
    suite = unittest.TestSuite()
    if onTestHost:
        suite.addTest(unittest.makeSuite(DbReadTests))
    return suite

if __name__ == '__main__' and onTestHost:
    unittest.main()

