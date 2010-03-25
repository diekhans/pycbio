import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.hgdata.Psl import Psl
from pycbio.hgdata.PslMap import PslMap

class MapTester(object):
    "test object that collects results"
    def __init__(self):
        self.mappings = []
        self.mapper = PslMap(self)

    def mapBlock(self, psl, blk, qRngStart, qRngEnd, tRngStart, tRngEnd):
        self.mappings.append(("blk", psl.qName, blk.iBlk, qRngStart, qRngEnd, tRngStart, tRngEnd))

    @staticmethod
    def __iBlkOrNone(blk):
        return blk.iBlk if blk != None else None

    def mapGap(self, psl, prevBlk, nextBlk, qRngStart, qRngEnd, tRngStart, tRngEnd):
        self.mappings.append(("gap", psl.qName, MapTester.__iBlkOrNone(prevBlk), MapTester.__iBlkOrNone(nextBlk), qRngStart, qRngEnd, tRngStart, tRngEnd))

    def __joinMappings(self):
        "join mappings into a tuple for testing and clear for next test"
        m = tuple(self.mappings)
        self.mappings = []
        return m

    def targetToQueryMap(self, psl, tRngStart, tRngEnd):
        self.mapper.targetToQueryMap(psl, tRngStart, tRngEnd)
        return self.__joinMappings()

    def queryToTargetMap(self, psl, qRngStart, qRngEnd):
        self.mapper.queryToTargetMap(psl, qRngStart, qRngEnd)
        return self.__joinMappings()

# test PSLs
_psPosMRna = "2515	2	0	0	0	0	16	26843	+	NM_012341	2537	0	2517	chr10	135374737	1024348	1053708	17	119,171,104,137,101,93,192,66,90,111,78,52,101,198,66,144,694,	0,119,290,394,531,632,725,917,983,1073,1184,1262,1314,1415,1613,1679,1823,	1024348,1028428,1031868,1032045,1033147,1034942,1036616,1036887,1041757,1042957,1044897,1045468,1046359,1048404,1050186,1051692,1053014,"

def splitToPsl(ps):
    return Psl(ps.split("\t"))
        
class TargetToQueryTests(TestCaseBase):
    def testPosMRna(self):
        mapper = MapTester()
        pslPosMrna = splitToPsl(_psPosMRna)
        # within a single block
        got = mapper.targetToQueryMap(pslPosMrna, 1024444, 1024445)
        self.failUnlessEqual(got, (('blk', 'NM_012341', 0, 96, 97, 1024444, 1024445),))
        # crossing gaps
        got = mapper.targetToQueryMap(pslPosMrna, 1024398, 1031918)
        self.failUnlessEqual(got, (('blk', 'NM_012341', 0, 50, 119, 1024398, 1024467),
                                   ('gap', 'NM_012341', 0, 1, None, None, 1024467, 1028428),
                                   ('blk', 'NM_012341', 1, 119, 290, 1028428, 1028599),
                                   ('gap', 'NM_012341', 1, 2, None, None, 1028599, 1031868),
                                   ('blk', 'NM_012341', 2, 290, 340, 1031868, 1031918)))
        # gap before
        got = mapper.targetToQueryMap(pslPosMrna, 1024309, 1028420)
        self.failUnlessEqual(got, (('gap', 'NM_012341', None, 0, None, None, 1024309, 1024348),
                                   ('blk', 'NM_012341', 0, 0, 119, 1024348, 1024467),
                                   ('gap', 'NM_012341', 0, 1, None, None, 1024467, 1028420)))
        # gap after
        got = mapper.targetToQueryMap(pslPosMrna, 1051793, 1053908)
        self.failUnlessEqual(got, (('blk', 'NM_012341', 15, 1780, 1823, 1051793, 1051836),
                                   ('gap', 'NM_012341', 15, 16, None, None, 1051836, 1053014),
                                   ('blk', 'NM_012341', 16, 1823, 2517, 1053014, 1053708),
                                   ('gap', 'NM_012341', 16, None, None, None, 1053708, 1053908)))

class QueryToTargetTests(TestCaseBase):
    def testPosMRna(self):
        mapper = MapTester()
        pslPosMrna = splitToPsl(_psPosMRna)
        # within a single block
        got = mapper.queryToTargetMap(pslPosMrna, 96, 97)
        self.failUnlessEqual(got, (('blk', 'NM_012341', 0, 96, 97, 1024444, 1024445),))
        # crossing gaps
        got = mapper.queryToTargetMap(pslPosMrna, 50, 340)
        self.failUnlessEqual(got, (('blk', 'NM_012341', 0, 50, 119, 1024398, 1024467),
                                   ('blk', 'NM_012341', 1, 119, 290, 1028428, 1028599),
                                   ('blk', 'NM_012341', 2, 290, 340, 1031868, 1031918)))
        # gap after
        got = mapper.queryToTargetMap(pslPosMrna, 1780, 2537)
        self.failUnlessEqual(got, (('blk', 'NM_012341', 15, 1780, 1823, 1051793, 1051836),
                                   ('blk', 'NM_012341', 16, 1823, 2517, 1053014, 1053708),
                                   ('gap', 'NM_012341', 16, None, 2517, 2537, None, None)))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TargetToQueryTests))
    suite.addTest(unittest.makeSuite(QueryToTargetTests))
    return suite

if __name__ == '__main__':
    unittest.main()

