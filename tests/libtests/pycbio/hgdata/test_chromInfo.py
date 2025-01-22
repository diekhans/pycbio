# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
import os.path as osp

if __name__ == '__main__':
    sys.path = ["../../../../lib", "../.."] + sys.path
from pycbio.hgdata.chromInfo import ChromInfoTbl
from pycbio.sys.testCaseBase import TestCaseBase
from testlib.mysqlCheck import mysqlTestsEnvAvailable, skip_if_no_mysql

if mysqlTestsEnvAvailable():
    from pycbio.hgdata.hgDb import connect

class ChromInfoTests(TestCaseBase):
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

    def _checkChroms(self, chroms):
        got10Chroms = tuple([(c.chrom, c.size)
                             for c in sorted(chroms.values(), key=lambda c: c.size, reverse=True)[0:10]])
        self.assertEqual(got10Chroms, self.expect10Chroms)

    def testLoadFile(self):
        chroms = ChromInfoTbl.loadFile(self.getInputFile("chrom.sizes"))
        self._checkChroms(chroms)

    @skip_if_no_mysql()
    def testLoadDb(self):
        hgdb = "hg38"
        with connect(hgdb) as conn:
            chroms = ChromInfoTbl.loadDb(conn)
            self._checkChroms(chroms)

    def testLoadTwoBit(self):
        hg38TwoBit = "/hive/data/genomes/hg38/hg38.2bit"
        if not osp.exists(hg38TwoBit):
            self.skipWarnTest(f"hg38 genome twoBit not found: {hg38TwoBit}")
        else:
            chroms = ChromInfoTbl.loadTwoBit(hg38TwoBit)
            self._checkChroms(chroms)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ChromInfoTests))
    return ts


if __name__ == '__main__':
    unittest.main()
