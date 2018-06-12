# Copyright 2006-2016 Mark Diekhans
"""
Test for storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.hgLite import sqliteConnect
from pycbio.db.sqliteOps import sqliteHaveTable
from pycbio.hgdata.hgLite import SequenceDbTable, Sequence, PslDbTable, GenePredDbTable
from pycbio.hgdata.hgLite import GencodeAttrs, GencodeAttrsDbTable, GencodeTranscriptSource, GencodeTranscriptSourceDbTable, GencodeTranscriptionSupportLevel, GencodeTranscriptionSupportLevelDbTable
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.genePred import GenePred


class SequenceTests(TestCaseBase):
    def testSequence(self):
        seq = Sequence("name1", "tagtcaaacccgtcgcctgcgcgaaa")
        self.assertEqual(">name1\ntagtcaaacccgtcgcctgcgcgaaa\n", seq.toFasta())


class SequenceDbTableTests(TestCaseBase):
    testData = (("name1", "gcctgcgcgaaacctccgctagtcaaacccgtccttagagcagtcgaaggg"),
                ("name2", "tagtcaaacccgtcgcctgcgcgaaacctccgccttagagcagtcgaaggg"),
                ("name3", "tagtcaaacccgtcgcctgcgcgaaa"),
                ("name4", "tagtcctccgccttagagcagtcgaaggg"))

    def setUp(self):
        self.conn = sqliteConnect(None)

    def tearDown(self):
        self.conn.close()
        self.conn = None

    def _loadTestSeqs(self):
        # try both tuple and sequence
        seqDb = SequenceDbTable(self.conn, "seqs", True)
        seqDb.loads([self.testData[0], Sequence(*self.testData[1]), Sequence(*self.testData[2]), self.testData[3]])
        seqDb.index()
        self.assertTrue(sqliteHaveTable(seqDb.conn, "seqs"))
        return seqDb

    def testSeqLoad(self):
        seqDb = self._loadTestSeqs()
        self.assertEqual(["name1", "name2", "name3", "name4"], sorted(seqDb.names()))
        self.assertEqual(Sequence(*self.testData[0]), seqDb.get("name1"))
        self.assertEqual(Sequence(*self.testData[1]), seqDb.get("name2"))
        self.assertEqual(None, seqDb.get("notthere"))

    def testRowRange(self):
        seqDb = self._loadTestSeqs()
        self.assertEqual(seqDb.getOidRange(), (1, 5))
        self.assertEqual(list(seqDb.getByOid(2, 4)), [Sequence(*self.testData[1]),
                                                      Sequence(*self.testData[2])])

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
    testData = ((24, 14, 224, 0, 5, 18, 7, 1109641, "-", "NM_144706.2", 1430, 1126, 1406, "chr22", 49554710, 16248348, 17358251, 9, "24,23,11,14,12,20,12,17,129", "24,48,72,85,111,123,145,157,175", "16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,"),
                (0, 10, 111, 0, 1, 13, 3, 344548, "+", "NM_025031.1", 664, 21, 155, "chr22", 49554710, 48109515, 48454184, 4, "17,11,12,81", "21,38,49,74", "48109515,48109533,48453547,48454103,"))

    @classmethod
    def _buildTestDb(cls, pslFile):
        conn = sqliteConnect(None)
        db = PslDbTable(conn, "aligns", True)
        db.loadPslFile(cls.getInputFile(pslFile))
        db.index()
        return conn, db

    @classmethod
    def setUpClass(cls):
        cls.clsConn, cls.pslTestDb = cls._buildTestDb("pslTest.psl")
        cls.strandConn, cls.strandTestDb = cls._buildTestDb("overlapingStrandCases.psl")

    @classmethod
    def tearDownClass(cls):
        cls.clsConn.close()
        cls.clsConn = cls.pslTestdb = None
        cls.strandConn.close()
        cls.strandConn = cls.strandTestDb = None

    def _makeObjCoords(self, psls):
        "return lists of qName and target coordinates for easy assert checking"
        return sorted([(psl.qName, psl.tName, psl.tStart, psl.tEnd, psl.strand) for psl in psls])

    def _makeRawCoords(self, rows):
        "return lists of qName and target coordinates for easy assert checking"
        return sorted([(row[9], row[13], row[15], row[16], row[8]) for row in rows])

    def testGetQName(self):
        psls = self.pslTestDb.getByQName("NM_000014.3")
        coords = self._makeObjCoords(psls)
        self.assertEqual(coords, [('NM_000014.3', 'chr1', 9111576, 9159754, '-'),
                                  ('NM_000014.3', 'chr12', 9111576, 9159754, '-')])
        psls = self.pslTestDb.getByQName("fred")
        self.assertEqual(psls, [])

    def testTRangeOverlap(self):
        psls = self.pslTestDb.getTRangeOverlap("chr1", 4268, 14754)
        expect = [('NM_182905.1', 'chr1', 4558, 7173, '-'),
                  ('NM_198943.1', 'chr1', 4268, 14754, '-')]
        coords = self._makeObjCoords(psls)
        self.assertEqual(coords, expect)

        rows = self.pslTestDb.getTRangeOverlap("chr1", 4268, 14754, raw=True)
        expect = [('NM_182905.1', 'chr1', 4558, 7173, '-'),
                  ('NM_198943.1', 'chr1', 4268, 14754, '-')]
        coords = self._makeRawCoords(rows)
        self.assertEqual(coords, expect)

    def testTRangeOverlapStrand(self):
        # data from overlapingStrandCases.psl
        psls = self.strandTestDb.getTRangeOverlap("chr1", 0, 80000, '-')
        expect = [('NR_024540', 'chr1', 14361, 29370, '-'),
                  ('NR_106918', 'chr1', 17368, 17436, '-'),
                  ('NR_107062', 'chr1', 17368, 17436, '-')]
        coords = self._makeObjCoords(psls)
        self.assertEqual(coords, expect)

        psls = self.strandTestDb.getTRangeOverlap("chr1", 0, 80000, ('+', '+-'))
        expect = [('NM_001006245', 'chr1', 14695, 24892, '+-'),
                  ('NM_001095143', 'chr1', 14695, 24850, '+-'),
                  ('NM_001105406', 'chr1', 14692, 24894, '+-'),
                  ('NM_001127390', 'chr1', 14695, 24892, '+-'),
                  ('NM_001244483', 'chr1', 14686, 24894, '+-'),
                  ('NR_046018', 'chr1', 11873, 14409, '+')]
        coords = self._makeObjCoords(psls)
        self.assertEqual(coords, expect)

    def testMemLoadPsl(self):
        conn = sqliteConnect(None)
        try:
            pslDb = PslDbTable(conn, "pslRows", True)
            pslDb.loads([Psl(self.testData[0]), Psl(self.testData[1])])
            pslDb.index()
            coords = self._makeObjCoords(pslDb.getByQName("NM_025031.1"))
            self.assertEqual(coords, [('NM_025031.1', 'chr22', 48109515, 48454184, '+')])
        finally:
            conn.close()

    def testMemLoadRow(self):
        conn = sqliteConnect(None)
        try:
            pslDb = PslDbTable(conn, "pslRows", True)
            pslDb.loads([self.testData[0], self.testData[1]])
            pslDb.index()
            coords = self._makeRawCoords(pslDb.getByQName("NM_025031.1", raw=True))
            self.assertEqual(coords, [('NM_025031.1', 'chr22', 48109515, 48454184, '+')])
        finally:
            conn.close()


class GenePredDbTableTests(TestCaseBase):
    testData = (("NM_000017.1", "chr12", "+", 119575618, 119589763, 119575641, 119589204, 10, "119575618,119576781,119586741,119587111,119587592,119588035,119588288,119588575,119588895,119589051,", "119575687,119576945,119586891,119587223,119587744,119588206,119588426,119588671,119588952,119589763,", 0, "one", "none", "none", "0,0,2,2,0,2,2,2,2,2,"),
                ("NM_000066.1", "chr1", "-", 56764802, 56801567, 56764994, 56801540, 12, "56764802,56767400,56768925,56776439,56779286,56781411,56785145,56787638,56790276,56792359,56795610,56801447,", "56765149,56767469,56769079,56776603,56779415,56781652,56785343,56787771,56790418,56792501,56795767,56801567,", 0, "two", "unk", "unk", "1,1,0,1,1,0,0,2,1,0,2,1,"),
                ("NM_000277.1", "chr12", "-", 101734570, 101813848, 101735419, 101813375, 13, "101734570,101736644,101739890,101740580,101743139,101747931,101749059,101751380,101762840,101773706,101790979,101809035,101813315,", "101735463,101736760,101740024,101740676,101743196,101748001,101749195,101751577,101762908,101773795,101791163,101809143,101813848,", 0, "five", "incmpl", "incmpl", "2,0,1,1,1,0,2,0,1,2,1,1,1,"))

    @classmethod
    def setUpClass(cls):
        cls.clsConn = sqliteConnect(None)
        cls.gpTestDb = GenePredDbTable(cls.clsConn, "refGene", True)
        cls.gpTestDb.loadGenePredFile(cls.getInputFile("fileFrameStatTest.gp"))
        cls.gpTestDb.index()

    @classmethod
    def tearDownClass(cls):
        cls.clsConn.close()
        cls.clsConn = cls.gpTestdb = None

    def _makeObjCoords(self, gps):
        "return lists of name and target coordinates for easy assert checking"
        return sorted([(gp.name, gp.chrom, gp.txStart, gp.txEnd, gp.strand) for gp in gps])

    def _makeRawCoords(self, rows):
        "return lists of name and target coordinates for easy assert checking"
        return sorted([(row[0], row[1], row[3], row[4], row[2]) for row in rows])

    def testGetName(self):
        gps = self.gpTestDb.getByName("NM_000017.1")
        coords = self._makeObjCoords(gps)
        self.assertEqual(coords, [("NM_000017.1", "chr12", 119575618, 119589763, '+')])
        gps = list(self.gpTestDb.getByName("fred"))
        self.assertEqual(gps, [])

    def testRangeOverlap(self):
        gps = self.gpTestDb.getRangeOverlap("chr12", 100000000, 200000000)
        expect = [("NM_000017.1", "chr12", 119575618, 119589763, '+'),
                  ("NM_000277.1", "chr12", 101734570, 101813848, '-')]
        coords = self._makeObjCoords(gps)
        self.assertEqual(coords, expect)

        rows = self.gpTestDb.getRangeOverlap("chr12", 100000000, 200000000, raw=True)
        coords = self._makeRawCoords(rows)
        self.assertEqual(coords, expect)

    def testRangeOverlapStrand(self):
        gps = self.gpTestDb.getRangeOverlap("chr12", 100000000, 800000000, strand='-')
        expect = [('NM_000277.1', 'chr12', 101734570, 101813848, '-')]
        coords = self._makeObjCoords(gps)
        self.assertEqual(coords, expect)

    def testMemLoadGenePred(self):
        conn = sqliteConnect(None)
        try:
            gpDb = GenePredDbTable(conn, "refGene", True)
            gpDb.loads([GenePred(self.testData[0]), GenePred(self.testData[1])])
            gpDb.index()
            coords = self._makeObjCoords(gpDb.getByName("NM_000017.1"))
            self.assertEqual(coords, [("NM_000017.1", "chr12", 119575618, 119589763, '+')])
        finally:
            conn.close()

    def testMemLoadRow(self):
        conn = sqliteConnect(None)
        try:
            gpDb = GenePredDbTable(conn, "refGene", True)
            gpDb.loads([self.testData[0], self.testData[1]])
            gpDb.index()
            coords = self._makeRawCoords(gpDb.getByName("NM_000017.1", raw=True))
            self.assertEqual(coords, [("NM_000017.1", "chr12", 119575618, 119589763, '+')])
        finally:
            conn.close()


class GencodeAttrsDbTableTests(TestCaseBase):
    # test have optional protein ids
    testData = (("ENSG00000187191.14", "DAZ3", "protein_coding", None, "ENST00000315357.9", "DAZ3-201", "protein_coding", None, "OTTHUMG00000045099.2", None, None, 3, "coding", "ENSP00000324965.7"),
                ("ENSG00000187191.14", "DAZ3", "protein_coding", None, "ENST00000382365.6", "DAZ3-001", "protein_coding", None, "OTTHUMG00000045099.2", "OTTHUMT00000104777.2", "CCDS35489.1", 2, "coding", "ENSP00000371802.2"),
                ("ENSG00000187191.14", "DAZ3", "protein_coding", None, "ENST00000446723.4", "DAZ3-202", "protein_coding", None, "OTTHUMG00000045099.2", None, None, 3, "coding", "ENSP00000401049.1"))

    # same with protein ids dropped
    testDataPrev = tuple((r[0:-1] for r in testData))

    @classmethod
    def setUpClass(cls):
        cls.clsConn = sqliteConnect(None)
        cls.attrsTestDb = GencodeAttrsDbTable(cls.clsConn, "gencodeAttrs", True)
        cls.attrsTestDb.loadTsv(cls.getInputFile("gencodeAttrs.tsv"))
        cls.attrsTestDb.index()

    @classmethod
    def tearDownClass(cls):
        cls.clsConn.close()
        cls.clsConn = cls.attrsTestDb = None

    def testGetTranscriptId(self):
        attrs = self.attrsTestDb.getByTranscriptId("ENST00000315357.9")
        self.assertEqual(attrs, GencodeAttrs(*self.testData[0]))
        attrs = self.attrsTestDb.getByTranscriptId("fred")
        self.assertEqual(attrs, None)

    def testGetNoProtId(self):
        conn = sqliteConnect(None)
        testDb = GencodeAttrsDbTable(conn, "gencodeAttrs", True)
        testDb.loadTsv(self.getInputFile("gencodeAttrsPrev.tsv"))
        testDb.index()
        attrs = testDb.getByTranscriptId("ENST00000315357.9")
        self.assertEqual(attrs, GencodeAttrs(*self.testDataPrev[0]))
        attrs = testDb.getByTranscriptId("ENST00000382365.6")
        self.assertEqual(attrs, GencodeAttrs(*self.testDataPrev[1]))

    def testGetGeneId(self):
        attrs = self.attrsTestDb.getByGeneId("ENSG00000187191.14")
        self.assertEqual(len(attrs), 3)
        attrs.sort(key=lambda a: a.transcriptId)
        self.assertEqual(attrs, [GencodeAttrs(*a) for a in self.testData])
        attrs = self.attrsTestDb.getByGeneId("fred")
        self.assertEqual(attrs, [])

    def testMemLoadGencodeAttrs(self):
        conn = sqliteConnect(None)
        try:
            db = GencodeAttrsDbTable(conn, "gencodeAttrs", True)
            db.loads([GencodeAttrs(*self.testData[0]), GencodeAttrs(*self.testData[1])])
            db.index()
            attrs = db.getByTranscriptId("ENST00000382365.6")
            self.assertEqual(attrs, GencodeAttrs(*self.testData[1]))
        finally:
            conn.close()


class GencodeTranscriptSourceDbTableTests(TestCaseBase):
    testData = (("ENST00000382365.6", "ensembl_havana_transcript"),
                ("ENST00000446723.4", "ensembl"),
                ("ENST00000315357.9", "ensembl"))

    @classmethod
    def setUpClass(cls):
        cls.clsConn = sqliteConnect(None)
        cls.transSrcTestDb = GencodeTranscriptSourceDbTable(cls.clsConn, "gencodeTranscriptSource", True)
        cls.transSrcTestDb.loadTsv(cls.getInputFile("gencodeTranscriptSource.tsv"))
        cls.transSrcTestDb.index()

    @classmethod
    def tearDownClass(cls):
        cls.clsConn.close()
        cls.clsConn = cls.gpTestdb = None

    def testGetTranscriptId(self):
        transSrc = self.transSrcTestDb.getByTranscriptId("ENST00000315357.9")
        self.assertEqual(transSrc, GencodeTranscriptSource(*self.testData[2]))
        transSrc = self.transSrcTestDb.getByTranscriptId("fred")
        self.assertEqual(transSrc, None)

    def testMemLoadGencodeTranscriptSource(self):
        conn = sqliteConnect(None)
        try:
            db = GencodeTranscriptSourceDbTable(conn, "gencodeTransSource", True)
            db.loads([GencodeTranscriptSource(*self.testData[0]), GencodeTranscriptSource(*self.testData[1])])
            db.index()
            transSrc = db.getByTranscriptId("ENST00000382365.6")
            self.assertEqual(transSrc, GencodeTranscriptSource(*self.testData[0]))
        finally:
            conn.close()


class GencodeTranscriptionSupportLevelDbTableTests(TestCaseBase):
    testData = (("ENST00000382365.6", 1),
                ("ENST00000446723.4", 1),
                ("ENST00000315357.9", 1))

    @classmethod
    def setUpClass(cls):
        cls.clsConn = sqliteConnect(None)
        cls.transSrcTestDb = GencodeTranscriptionSupportLevelDbTable(cls.clsConn, "gencodeTranscriptionSupportLevel", True)
        cls.transSrcTestDb.loadTsv(cls.getInputFile("gencodeTranscriptionSupportLevel.tsv"))
        cls.transSrcTestDb.index()

    @classmethod
    def tearDownClass(cls):
        cls.clsConn.close()
        cls.clsConn = cls.gpTestdb = None

    def testGetTranscriptId(self):
        transSrc = self.transSrcTestDb.getByTranscriptId("ENST00000315357.9")
        self.assertEqual(transSrc, GencodeTranscriptionSupportLevel(*self.testData[2]))
        transSrc = self.transSrcTestDb.getByTranscriptId("fred")
        self.assertEqual(transSrc, None)

    def testMemLoadGencodeTranscriptionSupportLevel(self):
        conn = sqliteConnect(None)
        try:
            db = GencodeTranscriptionSupportLevelDbTable(conn, "gencodeTransSource", True)
            db.loads([GencodeTranscriptionSupportLevel(*self.testData[0]), GencodeTranscriptionSupportLevel(*self.testData[1])])
            db.index()
            transSrc = db.getByTranscriptId("ENST00000382365.6")
            self.assertEqual(transSrc, GencodeTranscriptionSupportLevel(*self.testData[0]))
        finally:
            conn.close()


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(SequenceTests))
    ts.addTest(unittest.makeSuite(SequenceDbTableTests))
    ts.addTest(unittest.makeSuite(PslDbTableTests))
    ts.addTest(unittest.makeSuite(GenePredDbTableTests))
    ts.addTest(unittest.makeSuite(GencodeAttrsDbTableTests))
    ts.addTest(unittest.makeSuite(GencodeTranscriptSourceDbTableTests))
    ts.addTest(unittest.makeSuite(GencodeTranscriptionSupportLevelDbTableTests))
    return ts


if __name__ == '__main__':
    unittest.main()
