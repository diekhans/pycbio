# Copyright 2006-2016 Mark Diekhans
"""
Test for storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
import sqlite3
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.hgLite import SequenceLite, Sequence, PslLite
from pycbio.hgdata.psl import Psl


def memDbConnect():
    return sqlite3.connect(":memory:")


class SequenceTests(TestCaseBase):
    def testSequence(self):
        seq = Sequence("name1", "tagtcaaacccgtcgcctgcgcgaaa")
        self.assertEqual(seq.toFasta(), ">name1\ntagtcaaacccgtcgcctgcgcgaaa\n")


class SequenceLiteTests(TestCaseBase):
    __test1Seq = ("name1", "gcctgcgcgaaacctccgctagtcaaacccgtccttagagcagtcgaaggg")
    __test2Seq = ("name2", "tagtcaaacccgtcgcctgcgcgaaacctccgccttagagcagtcgaaggg")
    __test3Seq = ("name3", "tagtcaaacccgtcgcctgcgcgaaa")
    __test4Seq = ("name4", "tagtcctccgccttagagcagtcgaaggg")

    def setUp(self):
        self.conn = memDbConnect()

    def tearDown(self):
        self.conn.close()
        self.conn = None

    def __loadTestSeqs(self):
        # try both tuple and sequence
        seqDb = SequenceLite(self.conn, "seqs", True)
        seqDb.loads([self.__test1Seq, Sequence(*self.__test2Seq), Sequence(*self.__test3Seq), self.__test4Seq])
        seqDb.index()
        return seqDb

    def testSeqLoad(self):
        seqDb = self.__loadTestSeqs()
        self.assertEqual(sorted(seqDb.names()), ["name1", "name2", "name3", "name4"])
        self.assertEqual(seqDb.get("name1"), Sequence(*self.__test1Seq))
        self.assertEqual(seqDb.get("name2"), Sequence(*self.__test2Seq))

    def testRowRange(self):
        seqDb = self.__loadTestSeqs()
        self.assertEqual(seqDb.getOidRange(), (1, 5))
        self.assertEqual(list(seqDb.getRows(2, 4)), [Sequence(*self.__test2Seq),
                                                     Sequence(*self.__test3Seq)])


class PslLiteTests(TestCaseBase):
    testPsl1Row = (24, 14, 224, 0, 5, 18, 7, 1109641, "-", "NM_144706.2", 1430, 1126, 1406, "chr22", 49554710, 16248348, 17358251, 9, "24,23,11,14,12,20,12,17,129", "24,48,72,85,111,123,145,157,175", "16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,")
    testPsl2Row = (0, 10, 111, 0, 1, 13, 3, 344548, "+", "NM_025031.1", 664, 21, 155, "chr22", 49554710, 48109515, 48454184, 4, "17,11,12,81", "21,38,49,74", "48109515,48109533,48453547,48454103,")

    @classmethod
    def setUpClass(cls):
        # cache
        cls.pslTestDb = None
        cls.clsConn = None

    @classmethod
    def tearDownClass(cls):
        cls.pslTestdb = None
        if cls.clsConn is not None:
            cls.clsConn.close()
            cls.clsConn = None

    def setUp(self):
        if self.clsConn is None:
            # don't load for each test
            self.clsConn = memDbConnect()
            self.pslTestDb = PslLite(self.clsConn, "aligns", True)
            self.pslTestDb.loadPslFile(self.getInputFile("pslTest.psl"))
            self.pslTestDb.index()

    def __makeObjCoords(self, psls):
        "return lists of qName and target coordiates for easy assert checking"
        return sorted([(psl.qName, psl.tName, psl.tStart, psl.tEnd) for psl in psls])

    def __makeRawCoords(self, rows):
        "return lists of qName and target coordiates for easy assert checking"
        return sorted([(row[9], row[13], row[15], row[16]) for row in rows])

    def testGetQName(self):
        psls = self.pslTestDb.getByQName("NM_000014.3")
        coords = self.__makeObjCoords(psls)
        self.assertEqual(coords, [('NM_000014.3', 'chr1', 9111576, 9159754),
                                  ('NM_000014.3', 'chr12', 9111576, 9159754)])
        psls = self.pslTestDb.getByQName("fred")
        self.assertEqual(psls, [])

    def testTRangeOverlap(self):
        psls = self.pslTestDb.getTRangeOverlap("chr1", 4268, 14754)
        expect = [('NM_182905.1', 'chr1', 4558, 7173),
                  ('NM_198943.1', 'chr1', 4268, 14754)]
        coords = self.__makeObjCoords(psls)
        self.assertEqual(coords, expect)

        rows = self.pslTestDb.getTRangeOverlap("chr1", 4268, 14754, raw=True)
        expect = [('NM_182905.1', 'chr1', 4558, 7173),
                  ('NM_198943.1', 'chr1', 4268, 14754)]
        coords = self.__makeRawCoords(rows)
        self.assertEqual(coords, expect)

    def testMemLoadPsl(self):
        conn = memDbConnect()
        try:
            pslDb = PslLite(conn, "pslRows", True)
            pslDb.loads([Psl(self.testPsl1Row), Psl(self.testPsl2Row)])
            pslDb.index()
            coords = self.__makeObjCoords(pslDb.getByQName("NM_025031.1"))
            self.assertEqual(coords, [('NM_025031.1', 'chr22', 48109515, 48454184)])
        finally:
            conn.close()

    def testMemLoadRow(self):
        conn = memDbConnect()
        try:
            pslDb = PslLite(conn, "pslRows", True)
            pslDb.loads([self.testPsl1Row, self.testPsl2Row])
            pslDb.index()
            coords = self.__makeRawCoords(pslDb.getByQName("NM_025031.1", raw=True))
            self.assertEqual(coords, [('NM_025031.1', 'chr22', 48109515, 48454184)])
        finally:
            conn.close()


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(SequenceTests))
    ts.addTest(unittest.makeSuite(SequenceLiteTests))
    ts.addTest(unittest.makeSuite(PslLiteTests))
    return ts

if __name__ == '__main__':
    unittest.main()
