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
from pycbio.hgdata.hgLite import SequenceDbTable, Sequence, PslDbTable, GenePredDbTable, sqliteHaveTable
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.genePred import GenePred


def memDbConnect():
    return sqlite3.connect(":memory:")


class SequenceTests(TestCaseBase):
    def testSequence(self):
        seq = Sequence("name1", "tagtcaaacccgtcgcctgcgcgaaa")
        self.assertEqual(seq.toFasta(), ">name1\ntagtcaaacccgtcgcctgcgcgaaa\n")


class SequenceDbTableTests(TestCaseBase):
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
        seqDb = SequenceDbTable(self.conn, "seqs", True)
        seqDb.loads([self.__test1Seq, Sequence(*self.__test2Seq), Sequence(*self.__test3Seq), self.__test4Seq])
        seqDb.index()
        self.assertTrue(sqliteHaveTable(seqDb.conn, "seqs"))
        return seqDb

    def testSeqLoad(self):
        seqDb = self.__loadTestSeqs()
        self.assertEqual(sorted(seqDb.names()), ["name1", "name2", "name3", "name4"])
        self.assertEqual(seqDb.get("name1"), Sequence(*self.__test1Seq))
        self.assertEqual(seqDb.get("name2"), Sequence(*self.__test2Seq))
        self.assertEqual(seqDb.get("notthere"), None)

    def testRowRange(self):
        seqDb = self.__loadTestSeqs()
        self.assertEqual(seqDb.getOidRange(), (1, 5))
        self.assertEqual(list(seqDb.getRows(2, 4)), [Sequence(*self.__test2Seq),
                                                     Sequence(*self.__test3Seq)])

    def testLoadFasta(self):
        seqDb = SequenceDbTable(self.conn, "seqs", True)
        seqDb.loadFastaFile(self.getInputFile("ncbi.fa"))
        seqDb.index()
        self.assertEqual(sorted(seqDb.names()), ['AK289756.1', 'BG187649.1', 'NM_013266.2', 'U14680.1'])
        seq = seqDb.get("BG187649.1")
        self.assertEqual(seq.name, "BG187649.1")
        self.assertEqual(seq.seq,
                         "TGCCCAGATCCATCTTGTAAACAGGACTTGTTGGCCTACCTGGAACAGATTAAGTTCTACTCCCACCAAC"
                         "TGAAAATCTGCAGTCAAGTTAAAGCTGAGATCCAGAACCTGGGAGGAGAGCTCATCATGTCAGCTTTGGA"
                         "CAGTGTCACATCCCTGATCCAAGCAGCCAAAAATTTAATGAATGCTGTAGTGCAAACAGTGAAAATGTCT"
                         "TACATTGCCTCAACCAAGATCATCCGAATCCAGAGTCCTGCTGGGCCCCGGCACCCAGTTGTGATGTGGA"
                         "GAATGAAGGCTCCTGCAAAAAAACCCTTGATTAAAAGAGAGAAGCCAGAGGAAACGTGTGCAGCTGTCAG"
                         "ACGAGGCTCAGCAAAGAAAAAAATCCATCCATTGCAAGTCATGAGTGAATTTAGAGGAAGACAAATCTAC"
                         "TGAAACCACTATTCTACATATAGTGCCTATATGACAAAATCCTGCCTAACCACACTGCTTTATTTTACAC"
                         "TTAAGAAGTTCTGTAATTTCACTGAGTTTTGGTGTTTAACTCACAAATAACATAAAATATTGGGCGCTAA"
                         "ATCAACAAAAGCAATATATATTTGGGATCATATCACTGTCATTTCTGTATGGTCAGCACCCTATAGTTAA"
                         "GGAATATTTGCTTGTTGAATGAATGAAATTATCACGTGTTATTCACCGTTTCCCATAATAGAGATTATCT"
                         "ACTATTCGTTACCAAATAAACACAGGAGATGGCAGAGAGTCCGGTTTATCTGGAATCTTCATGTACCTTA"
                         "TAATCCTTACTTGAATTAAN")


class PslDbTableTests(TestCaseBase):
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
            self.pslTestDb = PslDbTable(self.clsConn, "aligns", True)
            self.pslTestDb.loadPslFile(self.getInputFile("pslTest.psl"))
            self.pslTestDb.index()

    def __makeObjCoords(self, psls):
        "return lists of qName and target coordinates for easy assert checking"
        return sorted([(psl.qName, psl.tName, psl.tStart, psl.tEnd) for psl in psls])

    def __makeRawCoords(self, rows):
        "return lists of qName and target coordinates for easy assert checking"
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
            pslDb = PslDbTable(conn, "pslRows", True)
            pslDb.loads([Psl(self.testPsl1Row), Psl(self.testPsl2Row)])
            pslDb.index()
            coords = self.__makeObjCoords(pslDb.getByQName("NM_025031.1"))
            self.assertEqual(coords, [('NM_025031.1', 'chr22', 48109515, 48454184)])
        finally:
            conn.close()

    def testMemLoadRow(self):
        conn = memDbConnect()
        try:
            pslDb = PslDbTable(conn, "pslRows", True)
            pslDb.loads([self.testPsl1Row, self.testPsl2Row])
            pslDb.index()
            coords = self.__makeRawCoords(pslDb.getByQName("NM_025031.1", raw=True))
            self.assertEqual(coords, [('NM_025031.1', 'chr22', 48109515, 48454184)])
        finally:
            conn.close()


class GenePredDbTableTests(TestCaseBase):
    testGenePred1Row = ("NM_000017.1", "chr12", "+", 119575618, 119589763, 119575641, 119589204, 10, "119575618,119576781,119586741,119587111,119587592,119588035,119588288,119588575,119588895,119589051,", "119575687,119576945,119586891,119587223,119587744,119588206,119588426,119588671,119588952,119589763,", 0, "one", "none", "none", "0,0,2,2,0,2,2,2,2,2,")
    testGenePred2Row = ("NM_000066.1", "chr1", "-", 56764802, 56801567, 56764994, 56801540, 12, "56764802,56767400,56768925,56776439,56779286,56781411,56785145,56787638,56790276,56792359,56795610,56801447,", "56765149,56767469,56769079,56776603,56779415,56781652,56785343,56787771,56790418,56792501,56795767,56801567,", 0, "two", "unk", "unk", "1,1,0,1,1,0,0,2,1,0,2,1,")

    @classmethod
    def setUpClass(cls):
        # cache
        cls.gpTestDb = None
        cls.clsConn = None

    @classmethod
    def tearDownClass(cls):
        cls.gpTestdb = None
        if cls.clsConn is not None:
            cls.clsConn.close()
            cls.clsConn = None

    def setUp(self):
        if self.clsConn is None:
            # don't load for each test
            self.clsConn = memDbConnect()
            self.gpTestDb = GenePredDbTable(self.clsConn, "refGene", True)
            self.gpTestDb.loadGenePredFile(self.getInputFile("fileFrameStatTest.gp"))
            self.gpTestDb.index()

    def __makeObjCoords(self, gps):
        "return lists of name and target coordinates for easy assert checking"
        return sorted([(gp.name, gp.chrom, gp.txStart, gp.txEnd) for gp in gps])

    def __makeRawCoords(self, rows):
        "return lists of name and target coordinates for easy assert checking"
        return sorted([(row[0], row[1], row[3], row[4]) for row in rows])

    def testGetName(self):
        gps = self.gpTestDb.getByName("NM_000017.1")
        coords = self.__makeObjCoords(gps)
        self.assertEqual(coords, [("NM_000017.1", "chr12", 119575618, 119589763)])
        gps = self.gpTestDb.getByName("fred")
        self.assertEqual(gps, [])

    def testRangeOverlap(self):
        gps = self.gpTestDb.getRangeOverlap("chr12", 100000000, 200000000)
        expect = [("NM_000017.1", "chr12", 119575618, 119589763),
                  ("NM_000277.1", "chr12", 101734570, 101813848)]
        coords = self.__makeObjCoords(gps)
        self.assertEqual(coords, expect)

        rows = self.gpTestDb.getRangeOverlap("chr12", 100000000, 200000000, raw=True)
        coords = self.__makeRawCoords(rows)
        self.assertEqual(coords, expect)

    def testMemLoadGenePred(self):
        conn = memDbConnect()
        try:
            gpDb = GenePredDbTable(conn, "refGene", True)
            gpDb.loads([GenePred(self.testGenePred1Row), GenePred(self.testGenePred2Row)])
            gpDb.index()
            coords = self.__makeObjCoords(gpDb.getByName("NM_000017.1"))
            self.assertEqual(coords, [("NM_000017.1", "chr12", 119575618, 119589763)])
        finally:
            conn.close()

    def testMemLoadRow(self):
        conn = memDbConnect()
        try:
            gpDb = GenePredDbTable(conn, "refGene", True)
            gpDb.loads([self.testGenePred1Row, self.testGenePred2Row])
            gpDb.index()
            coords = self.__makeRawCoords(gpDb.getByName("NM_000017.1", raw=True))
            self.assertEqual(coords, [("NM_000017.1", "chr12", 119575618, 119589763)])
        finally:
            conn.close()


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(SequenceTests))
    ts.addTest(unittest.makeSuite(SequenceDbTableTests))
    ts.addTest(unittest.makeSuite(PslDbTableTests))
    ts.addTest(unittest.makeSuite(GenePredDbTableTests))
    return ts

if __name__ == '__main__':
    unittest.main()