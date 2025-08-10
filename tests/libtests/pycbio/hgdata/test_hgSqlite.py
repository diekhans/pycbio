# Copyright 2006-2025 Mark Diekhans
"""
Test for storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
import sys
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.db import sqliteOps
from pycbio.hgdata.sequenceSqlite import SequenceSqliteTable, Sequence
from pycbio.hgdata.pslSqlite import PslSqliteTable
from pycbio.hgdata.genePredSqlite import GenePredSqliteTable
from pycbio.hgdata.gencodeSqlite import GencodeAttrs, GencodeAttrsSqliteTable, GencodeTranscriptSource, GencodeTranscriptSourceSqliteTable
from pycbio.hgdata.gencodeSqlite import GencodeTranscriptionSupportLevel, GencodeTranscriptionSupportLevelSqliteTable
from pycbio.hgdata.gencodeSqlite import GencodeToGeneSymbol, GencodeToGeneSymbolSqliteTable
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.genePred import genePredFromRow

###
# SequenceSqliteTable
###

@pytest.fixture
def conn():
    conn = sqliteOps.connect(None)
    yield conn
    conn.close()


seqTestData = (("name1", "gcctgcgcgaaacctccgctagtcaaacccgtccttagagcagtcgaaggg"),
               ("name2", "tagtcaaacccgtcgcctgcgcgaaacctccgccttagagcagtcgaaggg"),
               ("name3", "tagtcaaacccgtcgcctgcgcgaaa"),
               ("name4", "tagtcctccgccttagagcagtcgaaggg"))

def testSequence():
    seq = Sequence("name1", "tagtcaaacccgtcgcctgcgcgaaa")
    assert ">name1\ntagtcaaacccgtcgcctgcgcgaaa\n" == seq.toFasta()

def _loadTestSeqs(conn):
    # try both tuple and sequence
    seqTbl = SequenceSqliteTable(conn, "seqs", True)
    seqTbl.loads([seqTestData[0], Sequence(*seqTestData[1]), Sequence(*seqTestData[2]), seqTestData[3]])
    seqTbl.index()
    assert sqliteOps.haveTable(seqTbl.conn, "seqs")
    return seqTbl

def testSeqLoad(conn):
    seqTbl = _loadTestSeqs(conn)
    assert ["name1", "name2", "name3", "name4"] == sorted(seqTbl.names())
    assert Sequence(*seqTestData[0]) == seqTbl.get("name1")
    assert Sequence(*seqTestData[1]) == seqTbl.get("name2")
    assert seqTbl.get("notthere") is None

def testSeqRowRange(conn):
    seqTbl = _loadTestSeqs(conn)
    assert seqTbl.getOidRange() == (1, 5)
    assert list(seqTbl.getByOid(2, 4)) == [Sequence(*seqTestData[1]),
                                           Sequence(*seqTestData[2])]

def testSeqLoadFasta(request, conn):
    seqTbl = SequenceSqliteTable(conn, "seqs", True)
    seqTbl.loadFastaFile(ts.get_test_input_file(request, "ncbi.fa"))
    seqTbl.index()
    assert sorted(seqTbl.names()) == ['AK289756.1', 'BG187649.1', 'NM_013266.2', 'U14680.1']
    seq = seqTbl.get("BG187649.1")
    assert seq.name == "BG187649.1"
    assert seq.seq == ("TGCCCAGATCCATCTTGTAAACAGGACTTGTTGGCCTACCTGGAACAGATTAAGTTCTACTCCCACCAAC"
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


###
# PslSqliteTable
###
pslTestData = ((24, 14, 224, 0, 5, 18, 7, 1109641, "-", "NM_144706.2", 1430, 1126, 1406, "chr22", 49554710, 16248348, 17358251, 9, "24,23,11,14,12,20,12,17,129", "24,48,72,85,111,123,145,157,175", "16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,"),
               (0, 10, 111, 0, 1, 13, 3, 344548, "+", "NM_025031.1", 664, 21, 155, "chr22", 49554710, 48109515, 48454184, 4, "17,11,12,81", "21,38,49,74", "48109515,48109533,48453547,48454103,"))

def _buildTestDb(pslFile):
    conn = sqliteOps.connect(None)
    pslTbl = PslSqliteTable(conn, "aligns", True)
    pslTbl.loadPslFile(ts.get_test_session_input_file(__file__, pslFile))
    pslTbl.index()
    return conn, pslTbl

@pytest.fixture(scope="session")
def pslDb():
    conn, pslTbl = _buildTestDb("pslTest.psl")
    yield pslTbl
    conn.close()

@pytest.fixture(scope="session")
def pslStrandDb():
    conn, pslTbl = _buildTestDb("overlapingStrandCases.psl")
    yield pslTbl
    conn.close()

def _makePslObjCoords(psls):
    "return lists of qName and target coordinates for easy assert checking"
    return sorted([(psl.qName, psl.tName, psl.tStart, psl.tEnd, psl.strand) for psl in psls])

def _makePslRawCoords(rows):
    "return lists of qName and target coordinates for easy assert checking"
    return sorted([(row[9], row[13], row[15], row[16], row[8]) for row in rows])

def testPslGetQName(request, pslDb):
    psls = pslDb.getByQName("NM_000014.3")
    coords = _makePslObjCoords(psls)
    assert coords == [('NM_000014.3', 'chr1', 9111576, 9159754, '-'),
                      ('NM_000014.3', 'chr12', 9111576, 9159754, '-')]
    psls = pslDb.getByQName("fred")
    assert psls == []

def testPslTRangeOverlap(request, pslDb):
    psls = pslDb.getTRangeOverlap("chr1", 4268, 14754)
    expect = [('NM_182905.1', 'chr1', 4558, 7173, '-'),
              ('NM_198943.1', 'chr1', 4268, 14754, '-')]
    coords = _makePslObjCoords(psls)
    assert coords == expect

    rows = pslDb.getTRangeOverlap("chr1", 4268, 14754, raw=True)
    expect = [('NM_182905.1', 'chr1', 4558, 7173, '-'),
              ('NM_198943.1', 'chr1', 4268, 14754, '-')]
    coords = _makePslRawCoords(rows)
    assert coords == expect

def testPslTRangeOverlapStrand(request, pslStrandDb):
    # data from overlapingStrandCases.psl
    psls = pslStrandDb.getTRangeOverlap("chr1", 0, 80000, '-')
    expect = [('NR_024540', 'chr1', 14361, 29370, '-'),
              ('NR_106918', 'chr1', 17368, 17436, '-'),
              ('NR_107062', 'chr1', 17368, 17436, '-')]
    coords = _makePslObjCoords(psls)
    assert coords == expect

    psls = pslStrandDb.getTRangeOverlap("chr1", 0, 80000, ('+', '+-'))
    expect = [('NM_001006245', 'chr1', 14695, 24892, '+-'),
              ('NM_001095143', 'chr1', 14695, 24850, '+-'),
              ('NM_001105406', 'chr1', 14692, 24894, '+-'),
              ('NM_001127390', 'chr1', 14695, 24892, '+-'),
              ('NM_001244483', 'chr1', 14686, 24894, '+-'),
              ('NR_046018', 'chr1', 11873, 14409, '+')]
    coords = _makePslObjCoords(psls)
    assert coords == expect

def testPslMemLoadPsl():
    conn = sqliteOps.connect(None)
    try:
        tbl = PslSqliteTable(conn, "pslRows", True)
        tbl.loads([Psl.fromRow(p) for p in pslTestData])
        tbl.index()
        coords = _makePslObjCoords(tbl.getByQName("NM_025031.1"))
        assert coords == [('NM_025031.1', 'chr22', 48109515, 48454184, '+')]
    finally:
        conn.close()

def testPslMemLoadRow():
    conn = sqliteOps.connect(None)
    try:
        tbl = PslSqliteTable(conn, "pslRows", True)
        tbl.loads([pslTestData[0], pslTestData[1]])
        tbl.index()
        coords = _makePslRawCoords(tbl.getByQName("NM_025031.1", raw=True))
        assert coords == [('NM_025031.1', 'chr22', 48109515, 48454184, '+')]
    finally:
        conn.close()


##
# GenePredSqliteTable
##
gpTestData = (("NM_000017.1", "chr12", "+", 119575618, 119589763, 119575641, 119589204, 10, "119575618,119576781,119586741,119587111,119587592,119588035,119588288,119588575,119588895,119589051,", "119575687,119576945,119586891,119587223,119587744,119588206,119588426,119588671,119588952,119589763,", 0, "one", "none", "none", "0,0,2,2,0,2,2,2,2,2,"),
              ("NM_000066.1", "chr1", "-", 56764802, 56801567, 56764994, 56801540, 12, "56764802,56767400,56768925,56776439,56779286,56781411,56785145,56787638,56790276,56792359,56795610,56801447,", "56765149,56767469,56769079,56776603,56779415,56781652,56785343,56787771,56790418,56792501,56795767,56801567,", 0, "two", "unk", "unk", "1,1,0,1,1,0,0,2,1,0,2,1,"),
              ("NM_000277.1", "chr12", "-", 101734570, 101813848, 101735419, 101813375, 13, "101734570,101736644,101739890,101740580,101743139,101747931,101749059,101751380,101762840,101773706,101790979,101809035,101813315,", "101735463,101736760,101740024,101740676,101743196,101748001,101749195,101751577,101762908,101773795,101791163,101809143,101813848,", 0, "five", "incmpl", "incmpl", "2,0,1,1,1,0,2,0,1,2,1,1,1,"))

@pytest.fixture(scope="session")
def gpTbl():
    conn = sqliteOps.connect(None)
    gpTbl = GenePredSqliteTable(conn, "refGene", True)
    gpTbl.loadGenePredFile(ts.get_test_session_input_file(__file__, "fileFrameStatTest.gp"))
    gpTbl.index()
    yield gpTbl
    conn.close()

def _makeGpObjCoords(gps):
    "return lists of name and target coordinates for easy assert checking"
    return sorted([(gp.name, gp.chrom, gp.txStart, gp.txEnd, gp.strand) for gp in gps])

def _makeGpRawCoords(rows):
    "return lists of name and target coordinates for easy assert checking"
    return sorted([(row[0], row[1], row[3], row[4], row[2]) for row in rows])

def testGpGetName(request, gpTbl):
    gps = gpTbl.getByName("NM_000017.1")
    coords = _makeGpObjCoords(gps)
    assert coords == [("NM_000017.1", "chr12", 119575618, 119589763, '+')]
    gps = list(gpTbl.getByName("fred"))
    assert gps == []

def testGpRangeOverlap(request, gpTbl):
    gps = gpTbl.getRangeOverlap("chr12", 100000000, 200000000)
    expect = [("NM_000017.1", "chr12", 119575618, 119589763, '+'),
              ("NM_000277.1", "chr12", 101734570, 101813848, '-')]
    coords = _makeGpObjCoords(gps)
    assert coords == expect

    rows = gpTbl.getRangeOverlap("chr12", 100000000, 200000000, raw=True)
    coords = _makeGpRawCoords(rows)
    assert coords == expect

def testGpRangeOverlapStrand(request, gpTbl):
    gps = gpTbl.getRangeOverlap("chr12", 100000000, 800000000, strand='-')
    expect = [('NM_000277.1', 'chr12', 101734570, 101813848, '-')]
    coords = _makeGpObjCoords(gps)
    assert coords == expect

def testGpMemLoadGenePred():
    conn = sqliteOps.connect(None)
    try:
        tbl = GenePredSqliteTable(conn, "refGene", True)
        tbl.loads([genePredFromRow(r) for r in gpTestData])
        tbl.index()
        coords = _makeGpObjCoords(tbl.getByName("NM_000017.1"))
        assert coords == [("NM_000017.1", "chr12", 119575618, 119589763, '+')]
    finally:
        conn.close()

def testGpMemLoadRow():
    conn = sqliteOps.connect(None)
    try:
        tbl = GenePredSqliteTable(conn, "refGene", True)
        tbl.loads([gpTestData[0], gpTestData[1]])
        tbl.index()
        coords = _makeGpRawCoords(tbl.getByName("NM_000017.1", raw=True))
        assert coords == [("NM_000017.1", "chr12", 119575618, 119589763, '+')]
    finally:
        conn.close()


###
# GencodeAttrsSqliteTable
###
# test have optional protein ids
genAttrsTestData = (("ENSG00000187191.14", "DAZ3", "protein_coding", "ENST00000315357.9", "DAZ3-201", "protein_coding", None, 3, "coding", "ENSP00000324965.7"),
                    ("ENSG00000187191.14", "DAZ3", "protein_coding", "ENST00000382365.6", "DAZ3-001", "protein_coding", "CCDS35489.1", 2, "coding", "ENSP00000371802.2"),
                    ("ENSG00000187191.14", "DAZ3", "protein_coding", "ENST00000446723.4", "DAZ3-202", "protein_coding", None, 3, "coding", "ENSP00000401049.1"))

# same with protein ids dropped
genAttrsTestDataPrev = tuple((r[0:-1] for r in genAttrsTestData))

@pytest.fixture(scope="session")
def genAttrsTbl():
    conn = sqliteOps.connect(None)
    genAttrsTbl = GencodeAttrsSqliteTable(conn, "gencodeAttrs", True)
    genAttrsTbl.loadTsv(ts.get_test_session_input_file(__file__, "gencodeAttrs.tsv"))
    genAttrsTbl.index()
    yield genAttrsTbl
    conn.close()

def testGencodeAttrsGetTranscriptId(request, genAttrsTbl):
    attrs = genAttrsTbl.getByTranscriptId("ENST00000315357.9")
    assert attrs == GencodeAttrs(*genAttrsTestData[0])
    attrs = genAttrsTbl.getByTranscriptId("fred")
    assert attrs is None

def testGencodeAttrsGetNoProtId(request):
    conn = sqliteOps.connect(None)
    try:
        tbl = GencodeAttrsSqliteTable(conn, "gencodeAttrs", True)
        tbl.loadTsv(ts.get_test_input_file(request, "gencodeAttrsPrev.tsv"))
        tbl.index()
        attrs = tbl.getByTranscriptId("ENST00000315357.9")
        assert attrs == GencodeAttrs(*genAttrsTestDataPrev[0])
        attrs = tbl.getByTranscriptId("ENST00000382365.6")
        assert attrs == GencodeAttrs(*genAttrsTestDataPrev[1])
    finally:
        conn.close()

def testGencodeAttrsGetGeneId(request, genAttrsTbl):
    attrs = genAttrsTbl.getByGeneId("ENSG00000187191.14")
    assert len(attrs) == 3
    attrs.sort(key=lambda a: a.transcriptId)
    assert attrs == [GencodeAttrs(*a) for a in genAttrsTestData]
    attrs = genAttrsTbl.getByGeneId("fred")
    assert attrs == []

def testGencodeAttrsMemLoadGencodeAttrs():
    conn = sqliteOps.connect(None)
    try:
        tbl = GencodeAttrsSqliteTable(conn, "gencodeAttrs", True)
        tbl.loads([GencodeAttrs(*r) for r in genAttrsTestData])
        tbl.index()
        attrs = tbl.getByTranscriptId("ENST00000382365.6")
        assert attrs == GencodeAttrs(*genAttrsTestData[1])
    finally:
        conn.close()


###
# GencodeTranscriptSourceSqliteTable
###
genTransSrcTestData = (("ENST00000382365.6", "ensembl_havana_transcript"),
                       ("ENST00000446723.4", "ensembl"),
                       ("ENST00000315357.9", "ensembl"))

@pytest.fixture(scope="session")
def genTransSrcTbl():
    conn = sqliteOps.connect(None)
    genTransSrcTbl = GencodeTranscriptSourceSqliteTable(conn, "gencodeTranscriptSource", True)
    genTransSrcTbl.loadTsv(ts.get_test_session_input_file(__file__, "gencodeTranscriptSource.tsv"))
    genTransSrcTbl.index()
    yield genTransSrcTbl
    conn.close()

def testGencodeTransSrcGetTranscriptId(request, genTransSrcTbl):
    transSrc = genTransSrcTbl.getByTranscriptId("ENST00000315357.9")
    assert transSrc == GencodeTranscriptSource(*genTransSrcTestData[2])
    transSrc = genTransSrcTbl.getByTranscriptId("fred")
    assert transSrc is None

def testGencodeTranSrcMemLoad():
    conn = sqliteOps.connect(None)
    try:
        tbl = GencodeTranscriptSourceSqliteTable(conn, "gencodeTransSource", True)
        tbl.loads([GencodeTranscriptSource(*genTransSrcTestData[0]), GencodeTranscriptSource(*genTransSrcTestData[1])])
        tbl.index()
        transSrc = tbl.getByTranscriptId("ENST00000382365.6")
        assert transSrc == GencodeTranscriptSource(*genTransSrcTestData[0])
    finally:
        conn.close()


###
# GencodeTranscriptionSupportLevelSqliteTable
###
genSupportLevelTestData = (("ENST00000382365.6", 1),
                           ("ENST00000446723.4", 1),
                           ("ENST00000315357.9", 1))

@pytest.fixture(scope="session")
def genTransSupTbl():
    conn = sqliteOps.connect(None)
    genTransSupTbl = GencodeTranscriptionSupportLevelSqliteTable(conn, "gencodeTranscriptionSupportLevel", True)
    genTransSupTbl.loadTsv(ts.get_test_session_input_file(__file__, "gencodeTranscriptionSupportLevel.tsv"))
    genTransSupTbl.index()
    yield genTransSupTbl
    conn.close()

def testGencodeTransSupGetTranscriptId(request, genTransSupTbl):
    transSrc = genTransSupTbl.getByTranscriptId("ENST00000315357.9")
    assert transSrc == GencodeTranscriptionSupportLevel(*genSupportLevelTestData[2])
    transSrc = genTransSupTbl.getByTranscriptId("fred")
    assert transSrc is None

def testGencodeTransSupMemLoad():
    conn = sqliteOps.connect(None)
    try:
        tbl = GencodeTranscriptionSupportLevelSqliteTable(conn, "gencodeTransSource", True)
        tbl.loads([GencodeTranscriptionSupportLevel(*genSupportLevelTestData[0]), GencodeTranscriptionSupportLevel(*genSupportLevelTestData[1])])
        tbl.index()
        transSrc = tbl.getByTranscriptId("ENST00000382365.6")
        assert transSrc == GencodeTranscriptionSupportLevel(*genSupportLevelTestData[0])
    finally:
        conn.close()


###
# GencodeToGeneSymbolSqliteTable
###
genSymTestData = (("ENST00000538324.2", "ABO", "HGNC:79"),
                  ("ENST00000215794.8", "USP18", "HGNC:12616"),
                  ("ENST00000434390.1", "FAM230D", "HGNC:53910"))

@pytest.fixture(scope="session")
def genSymTbl():
    conn = sqliteOps.connect(None)
    genSymTbl = GencodeToGeneSymbolSqliteTable(conn, "gencodeToGeneSymbol", True)
    genSymTbl.loadTsv(ts.get_test_session_input_file(__file__, "gencodeToGeneSymbol.tsv"))
    genSymTbl.index()
    yield genSymTbl
    conn.close()

def testGencodeSymGetTranscriptId(request, genSymTbl):
    transSrc = genSymTbl.getByTranscriptId("ENST00000538324.2")
    assert transSrc == GencodeToGeneSymbol(*genSymTestData[0])
    transSrc = genSymTbl.getByTranscriptId("fred")
    assert transSrc is None

def testGencodeSymMemLoad():
    conn = sqliteOps.connect(None)
    try:
        tbl = GencodeToGeneSymbolSqliteTable(conn, "gencodeTransSource", True)
        tbl.loads([GencodeToGeneSymbol(*r) for r in genSymTestData])
        tbl.index()
        transSrc = tbl.getByTranscriptId("ENST00000434390.1")
        assert transSrc == GencodeToGeneSymbol(*genSymTestData[2])
    finally:
        conn.close()
