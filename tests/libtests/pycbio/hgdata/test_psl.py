# Copyright 2006-2025 Mark Diekhans
import sys
import pysam
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.sys import fileOps
from pycbio.hgdata.psl import Psl, PslTbl, pslFromCigar, pslFromPysam, reverseCoords, reverseStrand, dropQueryUniq

# test data as a string (ps = psl string)

psPos = "0	10	111	0	1	13	3	344548	+	NM_025031.1	664	21	155	chr22	49554710	48109515	48454184	4	17,11,12,81,	21,38,49,74,	48109515,48109533,48453547,48454103,"
psNeg = "24	14	224	0	5	18	7	1109641	-	NM_144706.2	1430	1126	1406	chr22	49554710	16248348	17358251	9	24,23,11,14,12,20,12,17,129,	24,48,72,85,111,123,145,157,175,	16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,"
psTransPosPos = "771	167	0	0	0	0	0	0	++	NM_001000369	939	1	939	chr1	245522847	52812	53750	1	938,	1,	52812,"
psTransPosNeg = "500	154	0	0	2	504	5	6805	+-	NM_001020776	1480	132	1290	chr1	245522847	92653606	92661065	6	57,84,30,135,164,184,	132,339,777,807,942,1106,	152861782,152862321,152864639,152864784,152866513,152869057,"
psTransNegPos = "71	5	0	0	1	93	2	213667	-+	AA608343.1a	186	0	169	chr5	180857866	157138232	157351975	3	27,29,20,	17,137,166,	157138232,157351058,157351955,"
psTransNegNeg = "47	4	0	0	1	122	1	46	--	AA608343.1b	186	5	178	chr6	170899992	29962882	29962979	2	30,21,	8,160,	140937013,140937089,"

def splitToPsl(ps):
    return Psl.fromRow(ps.split("\t"))

def testLoad(request):
    pslTbl = PslTbl(ts.get_test_input_file(request, "pslTest.psl"))
    assert len(pslTbl) == 14
    r = pslTbl[1]
    assert r.blockCount == 13
    assert len(r.blocks) == 13
    assert r.qName == "NM_198943.1"

def countQNameHits(pslTbl, qName):
    cnt = 0
    for p in pslTbl.getByQName(qName):
        assert p.qName == qName
        cnt += 1
    return cnt

def testQNameIdx(request):
    pslTbl = PslTbl(ts.get_test_input_file(request, "pslTest.psl"), qNameIdx=True)
    assert not pslTbl.haveQName("fred")
    assert pslTbl.haveQName("NM_001327.1")
    assert countQNameHits(pslTbl, "NM_198943.1") == 1
    assert countQNameHits(pslTbl, "fred") == 0
    assert countQNameHits(pslTbl, "NM_000014.3") == 2
    assert countQNameHits(pslTbl, "NM_001327.1") == 4

def testPslXCdsGenome(request):
    pslTbl = PslTbl(ts.get_test_input_file(request, "refseq.hg19.prot-genome.pslx"))
    assert len(pslTbl) == 4
    for psl in pslTbl:
        for blk in psl.blocks:
            assert len(blk.qSeq) == len(blk)
            assert len(blk.tSeq) == len(blk)

def _rcTest(psIn, psExpect):
    assert str(splitToPsl(psIn).reverseComplement()) == psExpect

def testReverseComplement():
    _rcTest(psPos, "0	10	111	0	1	13	3	344548	--	NM_025031.1	664	21	155	chr22	49554710	48109515	48454184	4	81,12,11,17,	509,603,615,626,	1100526,1101151,1445166,1445178,")
    _rcTest(psNeg, "24	14	224	0	5	18	7	1109641	+-	NM_144706.2	1430	1126	1406	chr22	49554710	16248348	17358251	9	129,17,12,20,12,14,11,23,24,	1126,1256,1273,1287,1307,1331,1347,1359,1382,	32196459,32196588,32263285,32491991,32500175,32643074,32778225,32942562,33306338,")
    _rcTest(psTransPosPos, "771	167	0	0	0	0	0	0	--	NM_001000369	939	1	939	chr1	245522847	52812	53750	1	938,	0,	245469097,")
    _rcTest(psTransPosNeg, "500	154	0	0	2	504	5	6805	-+	NM_001020776	1480	132	1290	chr1	245522847	92653606	92661065	6	184,164,135,30,84,57,	190,374,538,673,1057,1291,	92653606,92656170,92657928,92658178,92660442,92661008,")
    _rcTest(psTransNegPos, "71	5	0	0	1	93	2	213667	+-	AA608343.1a	186	0	169	chr5	180857866	157138232	157351975	3	20,29,27,	0,20,142,	23505891,23506779,23719607,")
    _rcTest(psTransNegNeg, "47	4	0	0	1	122	1	46	++	AA608343.1b	186	5	178	chr6	170899992	29962882	29962979	2	21,30,	5,148,	29962882,29962949,")

def _swapTest(psIn, psExpect):
    assert str(splitToPsl(psIn).swapSides(keepTStrandImplicit=True)) == psExpect

def testSwapSizes():
    _swapTest(psPos, "0	10	111	0	3	344548	1	13	+	chr22	49554710	48109515	48454184	NM_025031.1	664	21	155	4	17,11,12,81,	48109515,48109533,48453547,48454103,	21,38,49,74,")
    _swapTest(psNeg, "24	14	224	0	7	1109641	5	18	-	chr22	49554710	16248348	17358251	NM_144706.2	1430	1126	1406	9	129,17,12,20,12,14,11,23,24,	32196459,32196588,32263285,32491991,32500175,32643074,32778225,32942562,33306338,	1126,1256,1273,1287,1307,1331,1347,1359,1382,")
    _swapTest(psTransPosPos, "771	167	0	0	0	0	0	0	++	chr1	245522847	52812	53750	NM_001000369	939	1	939	1	938,	52812,	1,")
    _swapTest(psTransPosNeg, "500	154	0	0	5	6805	2	504	-+	chr1	245522847	92653606	92661065	NM_001020776	1480	132	1290	6	57,84,30,135,164,184,	152861782,152862321,152864639,152864784,152866513,152869057,	132,339,777,807,942,1106,")
    _swapTest(psTransNegPos, "71	5	0	0	2	213667	1	93	+-	chr5	180857866	157138232	157351975	AA608343.1a	186	0	169	3	27,29,20,	157138232,157351058,157351955,	17,137,166,")
    _swapTest(psTransNegNeg, "47	4	0	0	1	46	1	122	--	chr6	170899992	29962882	29962979	AA608343.1b	186	5	178	2	30,21,	140937013,140937089,	8,160,")

def _swapDropImplicitTest(psIn, psExpect):
    assert str(splitToPsl(psIn).swapSides(keepTStrandImplicit=False)) == psExpect

def testSwapSizesDropImplicit():
    _swapDropImplicitTest(psPos, "0	10	111	0	3	344548	1	13	++	chr22	49554710	48109515	48454184	NM_025031.1	664	21	155	4	17,11,12,81,	48109515,48109533,48453547,48454103,	21,38,49,74,")
    _swapDropImplicitTest(psNeg, "24	14	224	0	7	1109641	5	18	+-	chr22	49554710	16248348	17358251	NM_144706.2	1430	1126	1406	9	24,23,11,14,12,20,12,17,129,	16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,	24,48,72,85,111,123,145,157,175,")
    _swapDropImplicitTest(psTransPosPos, "771	167	0	0	0	0	0	0	++	chr1	245522847	52812	53750	NM_001000369	939	1	939	1	938,	52812,	1,")
    _swapDropImplicitTest(psTransPosNeg, "500	154	0	0	5	6805	2	504	-+	chr1	245522847	92653606	92661065	NM_001020776	1480	132	1290	6	57,84,30,135,164,184,	152861782,152862321,152864639,152864784,152866513,152869057,	132,339,777,807,942,1106,")
    _swapDropImplicitTest(psTransNegPos, "71	5	0	0	2	213667	1	93	+-	chr5	180857866	157138232	157351975	AA608343.1a	186	0	169	3	27,29,20,	157138232,157351058,157351955,	17,137,166,")
    _swapDropImplicitTest(psTransNegNeg, "47	4	0	0	1	46	1	122	--	chr6	170899992	29962882	29962979	AA608343.1b	186	5	178	2	30,21,	140937013,140937089,	8,160,")

def testCmpUniq():
    "check that PSL compares correctly"
    # set should product uniqueness
    psls = {splitToPsl(psPos),
            splitToPsl(psPos)}
    assert 1 == len(psls)

def testCalcStats():
    # 2618	0	0	0	0	0	2	3549
    # 2618	0	0	0	0	0	2	3549	+	ENST00000641515.2	2618	0	2618	chr1	248956422	65418	71585	3

    # sizes 15,54,2549,
    # q 0,15,69,
    # y 65418,65519,69036,

    psl = Psl(qName="ENST00000641515.2", qSize=2618, qStart=0, qEnd=2618,
              tName="chr1", tSize=248956422, tStart=65418, tEnd=71585, strand='+')
    psl.addBlock(0, 65418, 15)
    psl.addBlock(15, 65519, 54)
    psl.addBlock(69, 69036, 2549)
    psl.updateCounts()
    assert psl.match == 2618
    assert psl.tNumInsert == 2
    assert psl.tBaseInsert == 3549

def samParseHeader(row, chromSizes):
    # e@SQ	SN:chr1	LN:248956422
    if row[0] == "@SQ":
        chromSizes[row[1][3:]] = int(row[2][3:])

def samParseData(row, chromSizes):
    # qName, qStrand, tName, tSize, tPos, cigarStr
    # 0:QNAME, 1:FLAG 2:RNAME, 3:POS, 5:CIGAR
    return (row[0], '-' if (int(row[1]) & 0x10) else '+',
            row[2], chromSizes[row[2]], int(row[3]) - 1, row[5])

def samReader(bamFile):
    "return input to pslFromCigar"
    # doesn't depend on pysam, but just a quick hack
    chromSizes = {}
    for row in fileOps.iterRows(bamFile):
        if row[0][0] == '@':
            samParseHeader(row, chromSizes)
        else:
            yield samParseData(row, chromSizes)

def testOntSam(request):
    # use cigars from SMA file
    with open(ts.get_test_output_file(request, ".psl"), 'w') as fh:
        for args in samReader(ts.get_test_input_file(request, "ont-rna.sam")):
            pslFromCigar(*args).write(fh)
    ts.diff_results_expected(request, ".psl")

def testMultiMapSam(request):
    # use pysam
    # contains supplemental reads
    with (pysam.AlignmentFile(ts.get_test_input_file(request, "multimap.sam"), "r") as samfh,
          open(ts.get_test_output_file(request, ".psl"), 'w') as pslfh):
        for aln in samfh:
            pslFromPysam(samfh, aln).write(pslfh)
    ts.diff_results_expected(request, ".psl")

###
# Helper function tests
###
def testReverseCoords():
    """Test reverseCoords function"""
    assert reverseCoords(10, 20, 100) == (80, 90)
    assert reverseCoords(0, 50, 100) == (50, 100)
    assert reverseCoords(0, 100, 100) == (0, 100)

def testReverseStrand():
    """Test reverseStrand function"""
    assert reverseStrand('+') == '-'
    assert reverseStrand('-') == '+'

def testDropQueryUniq():
    """Test dropQueryUniq function"""
    assert dropQueryUniq("NM_001234") == "NM_001234"
    assert dropQueryUniq("NM_001234-1") == "NM_001234"
    assert dropQueryUniq("NM_001234-123") == "NM_001234"
    assert dropQueryUniq("NM_001234-1.5") == "NM_001234"

###
# PslBlock tests
###
def testPslBlockLen():
    """Test PslBlock.__len__"""
    psl = splitToPsl(psPos)
    assert len(psl.blocks[0]) == 17

def testPslBlockStr():
    """Test PslBlock.__str__"""
    psl = splitToPsl(psPos)
    blk = psl.blocks[0]
    assert str(blk) == f"{blk.qStart}..{blk.qEnd} <=> {blk.tStart}..{blk.tEnd}"

def testPslBlockPlusCoords():
    """Test PslBlock qStartPlus, qEndPlus, tStartPlus, tEndPlus"""
    # Positive strand PSL
    psl = splitToPsl(psPos)
    blk = psl.blocks[0]
    assert blk.qStartPlus == blk.qStart
    assert blk.qEndPlus == blk.qEnd
    assert blk.tStartPlus == blk.tStart
    assert blk.tEndPlus == blk.tEnd

    # Negative query strand PSL
    psl = splitToPsl(psNeg)
    blk = psl.blocks[0]
    # For negative strand, plus coords are reversed
    assert blk.qStartPlus == psl.qSize - blk.qEnd
    assert blk.qEndPlus == psl.qSize - blk.qStart

def testPslBlockSameAlign():
    """Test PslBlock.sameAlign"""
    psl1 = splitToPsl(psPos)
    psl2 = splitToPsl(psPos)
    assert psl1.blocks[0].sameAlign(psl2.blocks[0])
    assert not psl1.blocks[0].sameAlign(psl1.blocks[1])
    assert not psl1.blocks[0].sameAlign(None)

###
# Psl property tests
###
def testPslQLength():
    """Test Psl.qLength property"""
    psl = splitToPsl(psPos)
    assert psl.qLength == psl.qEnd - psl.qStart

def testPslTLength():
    """Test Psl.tLength property"""
    psl = splitToPsl(psPos)
    assert psl.tLength == psl.tEnd - psl.tStart

def testPslAlignSize():
    """Test Psl.alignSize property"""
    psl = splitToPsl(psPos)
    assert psl.alignSize == psl.match + psl.misMatch + psl.repMatch

def testPslQCover():
    """Test Psl.qCover property"""
    psl = splitToPsl(psPos)
    assert psl.qCover == psl.alignSize / psl.qSize

def testPslTCover():
    """Test Psl.tCover property"""
    psl = splitToPsl(psPos)
    assert psl.tCover == psl.alignSize / psl.tSize

def testPslQSpan():
    """Test Psl.qSpan property"""
    psl = splitToPsl(psPos)
    assert psl.qSpan == psl.qEnd - psl.qStart

def testPslTSpan():
    """Test Psl.tSpan property"""
    psl = splitToPsl(psPos)
    assert psl.tSpan == psl.tEnd - psl.tStart

def testPslIdentity():
    """Test Psl.identity method"""
    psl = splitToPsl(psPos)
    expected = (psl.match + psl.repMatch) / (psl.match + psl.misMatch + psl.repMatch)
    assert psl.identity() == expected

def testPslQDensity():
    """Test Psl.qDensity property"""
    psl = splitToPsl(psPos)
    assert psl.qDensity == psl.alignSize / psl.qSpan

def testPslTDensity():
    """Test Psl.tDensity property"""
    psl = splitToPsl(psPos)
    assert psl.tDensity == psl.alignSize / psl.tSpan

###
# Psl method tests
###
def testPslTOverlap():
    """Test Psl.tOverlap method"""
    psl = splitToPsl(psPos)
    # Overlapping
    assert psl.tOverlap(psl.tName, psl.tStart, psl.tEnd)
    assert psl.tOverlap(psl.tName, psl.tStart + 100, psl.tEnd - 100)
    # Non-overlapping
    assert not psl.tOverlap(psl.tName, 0, psl.tStart)
    assert not psl.tOverlap(psl.tName, psl.tEnd, psl.tEnd + 1000)
    # Different chromosome
    assert not psl.tOverlap("chrZ", psl.tStart, psl.tEnd)

def testPslSameAlign():
    """Test Psl.sameAlign method"""
    psl1 = splitToPsl(psPos)
    psl2 = splitToPsl(psPos)
    psl3 = splitToPsl(psNeg)
    assert psl1.sameAlign(psl2)
    assert not psl1.sameAlign(psl3)
    assert not psl1.sameAlign(None)

def testPslWrite(request):
    """Test Psl.write method"""
    psl = splitToPsl(psPos)
    outFile = ts.get_test_output_file(request, ".psl")
    with open(outFile, 'w') as fh:
        psl.write(fh)
    with open(outFile, 'r') as fh:
        line = fh.readline().strip()
    assert line == psPos

def testPslQueryKey():
    """Test Psl.queryKey static method"""
    psl = splitToPsl(psPos)
    key = Psl.queryKey(psl)
    assert key == (psl.qName, psl.qStart, psl.qEnd)

def testPslTargetKey():
    """Test Psl.targetKey static method"""
    psl = splitToPsl(psPos)
    key = Psl.targetKey(psl)
    assert key == (psl.tName, psl.tStart, psl.tEnd)

def testPslFromDictRow():
    """Test Psl.fromDictRow class method"""
    psl = splitToPsl(psPos)
    dictRow = {
        "qName": psl.qName, "qSize": psl.qSize, "qStart": psl.qStart, "qEnd": psl.qEnd,
        "tName": psl.tName, "tSize": psl.tSize, "tStart": psl.tStart, "tEnd": psl.tEnd,
        "strand": psl.strand,
        "matches": psl.match, "misMatches": psl.misMatch, "repMatches": psl.repMatch,
        "nCount": psl.nCount, "qNumInsert": psl.qNumInsert, "qBaseInsert": psl.qBaseInsert,
        "tNumInsert": psl.tNumInsert, "tBaseInsert": psl.tBaseInsert,
        "blockCount": psl.blockCount,
        "blockSizes": ",".join(str(b.size) for b in psl.blocks) + ",",
        "qStarts": ",".join(str(b.qStart) for b in psl.blocks) + ",",
        "tStarts": ",".join(str(b.tStart) for b in psl.blocks) + ",",
    }
    psl2 = Psl.fromDictRow(dictRow)
    assert psl.sameAlign(psl2)

###
# PslTbl tests
###
def testPslTblGetQNames(request):
    """Test PslTbl.getQNames method"""
    pslTbl = PslTbl(ts.get_test_input_file(request, "pslTest.psl"), qNameIdx=True)
    qNames = pslTbl.getQNames()
    assert isinstance(qNames, list)
    assert "NM_198943.1" in qNames

def testPslTblGetByQName(request):
    """Test PslTbl.getByQName method"""
    pslTbl = PslTbl(ts.get_test_input_file(request, "pslTest.psl"), qNameIdx=True)
    psls = pslTbl.getByQName("NM_001327.1")
    assert isinstance(psls, list)
    assert len(psls) == 4
    for psl in psls:
        assert psl.qName == "NM_001327.1"
