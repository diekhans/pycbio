# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
import pysam
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import fileOps
from pycbio.hgdata.psl import Psl, PslBlock, PslTbl, pslFromCigar, pslFromPysam

# test data as a string (ps = psl string)

psPos = "0	10	111	0	1	13	3	344548	+	NM_025031.1	664	21	155	chr22	49554710	48109515	48454184	4	17,11,12,81,	21,38,49,74,	48109515,48109533,48453547,48454103,"
psNeg = "24	14	224	0	5	18	7	1109641	-	NM_144706.2	1430	1126	1406	chr22	49554710	16248348	17358251	9	24,23,11,14,12,20,12,17,129,	24,48,72,85,111,123,145,157,175,	16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,"
psTransPosPos = "771	167	0	0	0	0	0	0	++	NM_001000369	939	1	939	chr1	245522847	52812	53750	1	938,	1,	52812,"
psTransPosNeg = "500	154	0	0	2	504	5	6805	+-	NM_001020776	1480	132	1290	chr1	245522847	92653606	92661065	6	57,84,30,135,164,184,	132,339,777,807,942,1106,	152861782,152862321,152864639,152864784,152866513,152869057,"
psTransNegPos = "71	5	0	0	1	93	2	213667	-+	AA608343.1a	186	0	169	chr5	180857866	157138232	157351975	3	27,29,20,	17,137,166,	157138232,157351058,157351955,"
psTransNegNeg = "47	4	0	0	1	122	1	46	--	AA608343.1b	186	5	178	chr6	170899992	29962882	29962979	2	30,21,	8,160,	140937013,140937089,"

def splitToPsl(ps):
    return Psl.fromRow(ps.split("\t"))

class ReadTests(TestCaseBase):
    def testLoad(self):
        pslTbl = PslTbl(self.getInputFile("pslTest.psl"))
        self.assertEqual(len(pslTbl), 14)
        r = pslTbl[1]
        self.assertEqual(r.blockCount, 13)
        self.assertEqual(len(r.blocks), 13)
        self.assertEqual(r.qName, "NM_198943.1")

    def countQNameHits(self, pslTbl, qName):
        cnt = 0
        for p in pslTbl.getByQName(qName):
            self.assertEqual(p.qName, qName)
            cnt += 1
        return cnt

    def testQNameIdx(self):
        pslTbl = PslTbl(self.getInputFile("pslTest.psl"), qNameIdx=True)
        self.assertFalse(pslTbl.haveQName("fred"))
        self.assertTrue(pslTbl.haveQName("NM_001327.1"))
        self.assertEqual(self.countQNameHits(pslTbl, "NM_198943.1"), 1)
        self.assertEqual(self.countQNameHits(pslTbl, "fred"), 0)
        self.assertEqual(self.countQNameHits(pslTbl, "NM_000014.3"), 2)
        self.assertEqual(self.countQNameHits(pslTbl, "NM_001327.1"), 4)

    def testPslXCdsGenome(self):
        pslTbl = PslTbl(self.getInputFile("refseq.hg19.prot-genome.pslx"))
        self.assertEqual(len(pslTbl), 4)
        for psl in pslTbl:
            for blk in psl.blocks:
                self.assertEqual(len(blk.qSeq), len(blk))
                self.assertEqual(len(blk.tSeq), len(blk))


class OpsTests(TestCaseBase):
    "test operations of PSL objects"

    def _rcTest(self, psIn, psExpect):
        self.assertEqual(str(splitToPsl(psIn).reverseComplement()), psExpect)

    def testReverseComplement(self):
        self._rcTest(psPos, "0	10	111	0	1	13	3	344548	--	NM_025031.1	664	21	155	chr22	49554710	48109515	48454184	4	81,12,11,17,	509,603,615,626,	1100526,1101151,1445166,1445178,")
        self._rcTest(psNeg, "24	14	224	0	5	18	7	1109641	+-	NM_144706.2	1430	1126	1406	chr22	49554710	16248348	17358251	9	129,17,12,20,12,14,11,23,24,	1126,1256,1273,1287,1307,1331,1347,1359,1382,	32196459,32196588,32263285,32491991,32500175,32643074,32778225,32942562,33306338,")
        self._rcTest(psTransPosPos, "771	167	0	0	0	0	0	0	--	NM_001000369	939	1	939	chr1	245522847	52812	53750	1	938,	0,	245469097,")
        self._rcTest(psTransPosNeg, "500	154	0	0	2	504	5	6805	-+	NM_001020776	1480	132	1290	chr1	245522847	92653606	92661065	6	184,164,135,30,84,57,	190,374,538,673,1057,1291,	92653606,92656170,92657928,92658178,92660442,92661008,")
        self._rcTest(psTransNegPos, "71	5	0	0	1	93	2	213667	+-	AA608343.1a	186	0	169	chr5	180857866	157138232	157351975	3	20,29,27,	0,20,142,	23505891,23506779,23719607,")
        self._rcTest(psTransNegNeg, "47	4	0	0	1	122	1	46	++	AA608343.1b	186	5	178	chr6	170899992	29962882	29962979	2	21,30,	5,148,	29962882,29962949,")

    def _swapTest(self, psIn, psExpect):
        self.assertEqual(str(splitToPsl(psIn).swapSides(keepTStrandImplicit=True)), psExpect)

    def testSwapSizes(self):
        self._swapTest(psPos, "0	10	111	0	3	344548	1	13	+	chr22	49554710	48109515	48454184	NM_025031.1	664	21	155	4	17,11,12,81,	48109515,48109533,48453547,48454103,	21,38,49,74,")
        self._swapTest(psNeg, "24	14	224	0	7	1109641	5	18	-	chr22	49554710	16248348	17358251	NM_144706.2	1430	1126	1406	9	129,17,12,20,12,14,11,23,24,	32196459,32196588,32263285,32491991,32500175,32643074,32778225,32942562,33306338,	1126,1256,1273,1287,1307,1331,1347,1359,1382,")
        self._swapTest(psTransPosPos, "771	167	0	0	0	0	0	0	++	chr1	245522847	52812	53750	NM_001000369	939	1	939	1	938,	52812,	1,")
        self._swapTest(psTransPosNeg, "500	154	0	0	5	6805	2	504	-+	chr1	245522847	92653606	92661065	NM_001020776	1480	132	1290	6	57,84,30,135,164,184,	152861782,152862321,152864639,152864784,152866513,152869057,	132,339,777,807,942,1106,")
        self._swapTest(psTransNegPos, "71	5	0	0	2	213667	1	93	+-	chr5	180857866	157138232	157351975	AA608343.1a	186	0	169	3	27,29,20,	157138232,157351058,157351955,	17,137,166,")
        self._swapTest(psTransNegNeg, "47	4	0	0	1	46	1	122	--	chr6	170899992	29962882	29962979	AA608343.1b	186	5	178	2	30,21,	140937013,140937089,	8,160,")

    def _swapDropImplicitTest(self, psIn, psExpect):
        self.assertEqual(str(splitToPsl(psIn).swapSides(keepTStrandImplicit=False)), psExpect)

    def testSwapSizesDropImplicit(self):
        self._swapDropImplicitTest(psPos, "0	10	111	0	3	344548	1	13	++	chr22	49554710	48109515	48454184	NM_025031.1	664	21	155	4	17,11,12,81,	48109515,48109533,48453547,48454103,	21,38,49,74,")
        self._swapDropImplicitTest(psNeg, "24	14	224	0	7	1109641	5	18	+-	chr22	49554710	16248348	17358251	NM_144706.2	1430	1126	1406	9	24,23,11,14,12,20,12,17,129,	16248348,16612125,16776474,16911622,17054523,17062699,17291413,17358105,17358122,	24,48,72,85,111,123,145,157,175,")
        self._swapDropImplicitTest(psTransPosPos, "771	167	0	0	0	0	0	0	++	chr1	245522847	52812	53750	NM_001000369	939	1	939	1	938,	52812,	1,")
        self._swapDropImplicitTest(psTransPosNeg, "500	154	0	0	5	6805	2	504	-+	chr1	245522847	92653606	92661065	NM_001020776	1480	132	1290	6	57,84,30,135,164,184,	152861782,152862321,152864639,152864784,152866513,152869057,	132,339,777,807,942,1106,")
        self._swapDropImplicitTest(psTransNegPos, "71	5	0	0	2	213667	1	93	+-	chr5	180857866	157138232	157351975	AA608343.1a	186	0	169	3	27,29,20,	157138232,157351058,157351955,	17,137,166,")
        self._swapDropImplicitTest(psTransNegNeg, "47	4	0	0	1	46	1	122	--	chr6	170899992	29962882	29962979	AA608343.1b	186	5	178	2	30,21,	140937013,140937089,	8,160,")

    def testCmpUniq(self):
        "check that PSL compares correctly"
        # set should product uniqueness
        psls = set([splitToPsl(psPos),
                    splitToPsl(psPos)])
        self.assertEqual(1, len(psls))

    def testCaclStats(self):
        # 2618	0	0	0	0	0	2	3549
        # 2618	0	0	0	0	0	2	3549	+	ENST00000641515.2	2618	0	2618	chr1	248956422	65418	71585	3

        # sizes 15,54,2549,
        # q 0,15,69,
        # y 65418,65519,69036,

        psl = Psl(qName="ENST00000641515.2", qSize=2618, qStart=0, qEnd=2618,
                  tName="chr1", tSize=248956422, tStart=65418, tEnd=71585, strand='+')
        psl.addBlock(PslBlock(0, 65418, 15))
        psl.addBlock(PslBlock(15, 65519, 54))
        psl.addBlock(PslBlock(69, 69036, 2549))
        psl.updateCounts()
        self.assertEqual(psl.match, 2618)
        self.assertEqual(psl.tNumInsert, 2)
        self.assertEqual(psl.tBaseInsert, 3549)

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

class MiniMapCigarTests(TestCaseBase):
    "Minimap cigar to PSL tests"

    def testOntSam(self):
        # use cigars from SMA file
        with open(self.getOutputFile(".psl"), 'w') as fh:
            for args in samReader(self.getInputFile("ont-rna.sam")):
                pslFromCigar(*args).write(fh)
        self.diffExpected(".psl")

    def testMultiMapSam(self):
        # use pysam
        # contains supplemental reads
        with (pysam.AlignmentFile(self.getInputFile("multimap.sam"), "r") as samfh,
              open(self.getOutputFile(".psl"), 'w') as pslfh):
            for aln in samfh:
                pslFromPysam(samfh, aln).write(pslfh)
        self.diffExpected(".psl")

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ReadTests))
    ts.addTest(unittest.makeSuite(OpsTests))
    ts.addTest(unittest.makeSuite(MiniMapCigarTests))
    return ts


if __name__ == '__main__':
    unittest.main()
