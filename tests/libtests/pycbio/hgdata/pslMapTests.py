# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.pslMap import PslMap


##
# test PSLs
##
_pslPosMRna = "2515	2	0	0	0	0	16	26843	+	NM_012341	2537	0	2517	chr10	135374737	1024348	1053708	17	119,171,104,137,101,93,192,66,90,111,78,52,101,198,66,144,694,	0,119,290,394,531,632,725,917,983,1073,1184,1262,1314,1415,1613,1679,1823,	1024348,1028428,1031868,1032045,1033147,1034942,1036616,1036887,1041757,1042957,1044897,1045468,1046359,1048404,1050186,1051692,1053014,"
_pslDoubleDel1 = "1226	150	0	0	0	0	0	0	-	NM_017069.1-1.1	1792	8	1387	chrX	154913754	151108857	151370996	12	212,153,144,83,221,68,118,4,182,2,169,20,	405,617,770,914,997,1218,1286,1404,1408,1591,1593,1764,	151108857,151116760,151127128,151143890,151174905,151203795,151264708,151264832,151283558,151370804,151370807,151370976,"
_pslDoubleDel2 = "298	106	0	0	0	0	0	0	-	DQ216042.1-1.1	1232	53	593	chrX	154913754	151747020	151748962	5	18,65,22,138,161,	639,658,729,751,1018,	151747020,151747038,151747108,151747736,151748801,"
_pslNegMrna = "5148	0	415	0	0	0	27	208231	-	NM_017651	5564	0	5563	chr6	171115067	135605109	135818903	28	1676,103,59,98,163,56,121,27,197,141,131,119,107,230,124,133,153,186,96,193,220,182,560,54,125,64,62,183,	1,1677,1780,1839,1937,2100,2156,2277,2304,2501,2642,2773,2892,2999,3229,3353,3486,3639,3825,3921,4114,4334,4516,5076,5130,5255,5319,5381,	135605109,135611560,135621637,135639656,135644299,135679269,135715913,135726088,135732485,135748304,135749766,135751019,135752345,135754164,135759512,135763719,135768145,135769427,135774478,135776871,135778631,135784262,135786951,135788718,135811760,135813365,135818325,135818720,"  # noqa
_pslAugustusBlat = "39	0	0	0	0	0	1	3	-	jg18564.t1::chr12:78274203-78324771(+)	972	123	162	19	61431566	38013595	38013637	2	18,21,	810,828,	38013595,38013616,"


def splitToPsl(line):
    return Psl.fromRow(line.split("\t"))

def _mapToTuple(pmr):
    typ = "blk" if (pmr.qStart is not None) and (pmr.tStart is not None) else "gap"
    return (typ, pmr.qPrevEnd, pmr.qStart, pmr.qEnd, pmr.qNextStart, pmr.qStrand, pmr.tPrevEnd, pmr.tStart, pmr.tEnd, pmr.tNextStart, pmr.tStrand)

def _targetToQueryMap(mapPsl, tRngStart, tRngEnd, tStrand=None):
    return tuple([_mapToTuple(m) for m in PslMap(mapPsl).targetToQueryMap(tRngStart, tRngEnd, tStrand)])

def _queryToTargetMap(mapPsl, qRngStart, qRngEnd, qStrand=None):
    return tuple([_mapToTuple(m) for m in PslMap(mapPsl).queryToTargetMap(qRngStart, qRngEnd, qStrand)])

class TargetToQueryTests(TestCaseBase):
    def testPosMRna(self):
        psl = splitToPsl(_pslPosMRna)
        # within a single block
        got = _targetToQueryMap(psl, 1024444, 1024445)
        self.assertEqual((('blk', None, 96, 97, None, '+', None, 1024444, 1024445, None, '+'),),
                         got)

        # crossing gaps
        got = _targetToQueryMap(psl, 1024398, 1031918)
        self.assertEqual((('blk', None, 50, 119, None, '+', None, 1024398, 1024467, None, '+'),
                          ('gap', 119, None, None, 119, '+', None, 1024467, 1028428, None, '+'),
                          ('blk', None, 119, 290, None, '+', None, 1028428, 1028599, None, '+'),
                          ('gap', 290, None, None, 290, '+', None, 1028599, 1031868, None, '+'),
                          ('blk', None, 290, 340, None, '+', None, 1031868, 1031918, None, '+')),
                         got)

        # crossing gaps, with strand reversal
        got = _targetToQueryMap(psl, 134342819, 134350339, tStrand='-')  # 1024398-1031918 on - strand
        self.assertEqual((('blk', None, 50, 119, None, '+', None, 134350270, 134350339, None, '-'),
                          ('gap', 119, None, None, 119, '+', None, 134346309, 134350270, None, '-'),
                          ('blk', None, 119, 290, None, '+', None, 134346138, 134346309, None, '-'),
                          ('gap', 290, None, None, 290, '+', None, 134342869, 134346138, None, '-'),
                          ('blk', None, 290, 340, None, '+', None, 134342819, 134342869, None, '-')),
                         got)

        # gap before
        got = _targetToQueryMap(psl, 1024309, 1028420)
        self.assertEqual(got, (('gap', None, None, None, 0, '+', None, 1024309, 1024348, None, '+'),
                               ('blk', None, 0, 119, None, '+', None, 1024348, 1024467, None, '+'),
                               ('gap', 119, None, None, 119, '+', None, 1024467, 1028420, None, '+')))

        # gap after
        got = _targetToQueryMap(psl, 1051793, 1053908)
        self.assertEqual((('blk', None, 1780, 1823, None, '+', None, 1051793, 1051836, None, '+'),
                          ('gap', 1823, None, None, 1823, '+', None, 1051836, 1053014, None, '+'),
                          ('blk', None, 1823, 2517, None, '+', None, 1053014, 1053708, None, '+'),
                          ('gap', 2517, None, None, None, '+', None, 1053708, 1053908, None, '+')),
                         got)

    def testDoubleDel1(self):
        "gap with deletions on both sizes, query one a single base"
        psl = splitToPsl(_pslDoubleDel1)
        got = _targetToQueryMap(psl, 151283730, 151370810)
        self.assertEqual((('blk', None, 1580, 1590, None, '-', None, 151283730, 151283740, None, '+'),
                          ('gap', 1590, None, None, 1591, '-', None, 151283740, 151370804, None, '+'),
                          ('blk', None, 1591, 1593, None, '-', None, 151370804, 151370806, None, '+'),
                          ('gap', 1593, None, None, 1593, '-', None, 151370806, 151370807, None, '+'),
                          ('blk', None, 1593, 1596, None, '-', None, 151370807, 151370810, None, '+')),
                         got)
        got = _queryToTargetMap(psl, 1408, 1784)
        self.assertEqual((('blk', None, 1408, 1590, None, '-', None, 151283558, 151283740, None, '+'),
                          ('gap', None, 1590, 1591, None, '-', 151283740, None, None, 151370804, '+'),
                          ('blk', None, 1591, 1593, None, '-', None, 151370804, 151370806, None, '+'),
                          ('blk', None, 1593, 1762, None, '-', None, 151370807, 151370976, None, '+'),
                          ('gap', None, 1762, 1764, None, '-', 151370976, None, None, 151370976, '+'),
                          ('blk', None, 1764, 1784, None, '-', None, 151370976, 151370996, None, '+')),
                         got)

    def testDoubleDel1ToPsl(self):
        "gap with deletions on both sizes, query one a single base, to a PSL"
        mapPsl = splitToPsl(_pslDoubleDel1)
        gotPsl = PslMap(mapPsl).targetToQueryMapPsl(151283730, 151370810)
        self.assertEqual(['15', '0', '0', '0', '1', '1', '2', '87065', '-', 'NM_017069.1-1.1', '1792', '196', '212', 'chrX', '154913754', '151283730', '151370810', '3', '10,2,3,', '1580,1591,1593,', '151283730,151370804,151370807,'],
                         gotPsl.toRow())
        gotPsl = PslMap(mapPsl).queryToTargetMapPsl(151283730, 151370810)
        self.assertEqual(None, gotPsl)

class QueryToTargetTests(TestCaseBase):
    def testPosMRna(self):
        psl = splitToPsl(_pslPosMRna)
        # within a single block
        got = _queryToTargetMap(psl, 96, 97)
        self.assertEqual(got, (('blk', None, 96, 97, None, '+', None, 1024444, 1024445, None, '+'),))

        # crossing gaps
        got = _queryToTargetMap(psl, 50, 340)
        self.assertEqual((('blk', None, 50, 119, None, '+', None, 1024398, 1024467, None, '+'),
                          ('blk', None, 119, 290, None, '+', None, 1028428, 1028599, None, '+'),
                          ('blk', None, 290, 340, None, '+', None, 1031868, 1031918, None, '+')),
                         got)

        # gap after
        got = _queryToTargetMap(psl, 1780, 2537)
        self.assertEqual((('blk', None, 1780, 1823, None, '+', None, 1051793, 1051836, None, '+'),
                          ('blk', None, 1823, 2517, None, '+', None, 1053014, 1053708, None, '+'),
                          ('gap', None, 2517, 2537, None, '+', 1053708, None, None, None, '+')),
                         got)

    def testNegMRna(self):
        # One-base gap at query start of negative strand PSL.  This appeared to be a bug,
        # but it is doing the right thing.

        # within a single block and on neg strand
        pslNegMrna = splitToPsl(_pslNegMrna)
        got = _queryToTargetMap(pslNegMrna, 0, 100)
        self.assertEqual((('gap', None, 0, 1, None, '-', None, None, None, 135605109, '+'),
                          ('blk', None, 1, 100, None, '-', None, 135605109, 135605208, None, '+')),
                         got)

    def testNegMRnaToPsl(self):
        # within a single block and on neg strand
        pslNegMrna = splitToPsl(_pslNegMrna)
        gotPsl = PslMap(pslNegMrna).queryToTargetMapPsl(0, 100)
        self.assertEqual(['99', '0', '0', '0', '0', '0', '0', '0', '-', 'NM_017651', '5564', '5464', '5563', 'chr6', '171115067', '135605109', '135605208', '1', '99,', '1,', '135605109,'],
                         gotPsl.toRow())

    def testDoubleDel1(self):
        "gap with deletions on both sizes, query one a single base"
        psl = splitToPsl(_pslDoubleDel1)
        # this includes query deletion on either end
        got = _queryToTargetMap(psl, 3, 1790, qStrand='+')
        self.assertEqual((('gap', None, 1387, 1790, None, '+', None, None, None, 151108857, '+'),
                          ('blk', None, 1175, 1387, None, '+', None, 151108857, 151109069, None, '+'),
                          ('blk', None, 1022, 1175, None, '+', None, 151116760, 151116913, None, '+'),
                          ('blk', None, 878, 1022, None, '+', None, 151127128, 151127272, None, '+'),
                          ('blk', None, 795, 878, None, '+', None, 151143890, 151143973, None, '+'),
                          ('blk', None, 574, 795, None, '+', None, 151174905, 151175126, None, '+'),
                          ('blk', None, 506, 574, None, '+', None, 151203795, 151203863, None, '+'),
                          ('blk', None, 388, 506, None, '+', None, 151264708, 151264826, None, '+'),
                          ('blk', None, 384, 388, None, '+', None, 151264832, 151264836, None, '+'),
                          ('blk', None, 202, 384, None, '+', None, 151283558, 151283740, None, '+'),
                          ('gap', None, 201, 202, None, '+', 151283740, None, None, 151370804, '+'),
                          ('blk', None, 199, 201, None, '+', None, 151370804, 151370806, None, '+'),
                          ('blk', None, 30, 199, None, '+', None, 151370807, 151370976, None, '+'),
                          ('gap', None, 28, 30, None, '+', 151370976, None, None, 151370976, '+'),
                          ('blk', None, 8, 28, None, '+', None, 151370976, 151370996, None, '+'),
                          ('gap', None, 3, 8, None, '+', 151370996, None, None, None, '+')),
                         got)
        got = _queryToTargetMap(psl, 2, 1789)  # same range as 3-1790 on - strand
        self.assertEqual((('gap', None, 2, 405, None, '-', None, None, None, 151108857, '+'),
                          ('blk', None, 405, 617, None, '-', None, 151108857, 151109069, None, '+'),
                          ('blk', None, 617, 770, None, '-', None, 151116760, 151116913, None, '+'),
                          ('blk', None, 770, 914, None, '-', None, 151127128, 151127272, None, '+'),
                          ('blk', None, 914, 997, None, '-', None, 151143890, 151143973, None, '+'),
                          ('blk', None, 997, 1218, None, '-', None, 151174905, 151175126, None, '+'),
                          ('blk', None, 1218, 1286, None, '-', None, 151203795, 151203863, None, '+'),
                          ('blk', None, 1286, 1404, None, '-', None, 151264708, 151264826, None, '+'),
                          ('blk', None, 1404, 1408, None, '-', None, 151264832, 151264836, None, '+'),
                          ('blk', None, 1408, 1590, None, '-', None, 151283558, 151283740, None, '+'),
                          ('gap', None, 1590, 1591, None, '-', 151283740, None, None, 151370804, '+'),
                          ('blk', None, 1591, 1593, None, '-', None, 151370804, 151370806, None, '+'),
                          ('blk', None, 1593, 1762, None, '-', None, 151370807, 151370976, None, '+'),
                          ('gap', None, 1762, 1764, None, '-', 151370976, None, None, 151370976, '+'),
                          ('blk', None, 1764, 1784, None, '-', None, 151370976, 151370996, None, '+'),
                          ('gap', None, 1784, 1789, None, '-', 151370996, None, None, None, '+')),
                         got)

    def testFullQueryMap(self):
        # Mapping through PSL produced by BLATing an augustus mouse strain
        # prediction.  When traversing source exon rages ranges, it produced
        # incorrect query coordinates when there is a gap at the end and starting
        # coordinates were in the middle of the gap.
        queryExonRanges = ((0, 3744), (3744, 4172), (4172, 4308), (4308, 4506),
                           (4506, 4569), (4569, 4787), (4787, 5002))
        mapper = PslMap(splitToPsl(_pslAugustusBlat))
        got = []
        for rng in queryExonRanges:
            got.extend([_mapToTuple(m) for m in mapper.queryToTargetMap(rng[0], rng[1])])
        got = tuple(got)
        self.assertEqual((('gap', None, 0, 810, None, '-', None, None, None, 38013595, '+'),
                          ('blk', None, 810, 828, None, '-', None, 38013595, 38013613, None, '+'),
                          ('blk', None, 828, 849, None, '-', None, 38013616, 38013637, None, '+'),
                          ('gap', None, 849, 3744, None, '-', 38013637, None, None, None, '+'),
                          ('gap', None, 3744, 4172, None, '-', 38013637, None, None, None, '+'),
                          ('gap', None, 4172, 4308, None, '-', 38013637, None, None, None, '+'),
                          ('gap', None, 4308, 4506, None, '-', 38013637, None, None, None, '+'),
                          ('gap', None, 4506, 4569, None, '-', 38013637, None, None, None, '+'),
                          ('gap', None, 4569, 4787, None, '-', 38013637, None, None, None, '+'),
                          ('gap', None, 4787, 5002, None, '-', 38013637, None, None, None, '+')),
                         got)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(TargetToQueryTests))
    ts.addTest(unittest.makeSuite(QueryToTargetTests))
    return ts


if __name__ == '__main__':
    unittest.main()
