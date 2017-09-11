# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.gff3 import Gff3Parser


class Gff3Tests(TestCaseBase):
    def __countRows(self, gff3File):
        cnt = 0
        with open(gff3File) as fh:
            for line in fh:
                if line[0].isalnum():
                    cnt += 1
        return cnt

    def __write(self, gff3, outGff3):
        with open(outGff3, "w") as fh:
            gff3.write(fh)

    def __parseTest(self, gff3RelIn):
        # parse and write
        gff3a = Gff3Parser(self.getInputFile(gff3RelIn)).parse()
        gff3Out1 = self.getOutputFile(".gff3")
        self.__write(gff3a, gff3Out1)
        self.assertEquals(self.__countRows(gff3a.fileName), self.__countRows(gff3Out1))
        self.diffExpected(".gff3")
        gff3b = Gff3Parser(self.getInputFile(gff3RelIn)).parse()
        gff3Out2 = self.getOutputFile(".2.gff3")
        self.__write(gff3b, gff3Out2)
        self.diffFiles(self.getExpectedFile(".gff3"), self.getOutputFile(".2.gff3"))
        return gff3a

    def testSacCer(self):
        gff3a = self.__parseTest("sacCerTest.gff3")
        #  gene	335	649
        feats = gff3a.byFeatureId["YAL069W"]
        self.assertEquals(len(feats), 1)
        # check that it is zero-based internally
        self.assertEquals(feats[0].start, 334)
        self.assertEquals(feats[0].end, 649)

    def testSpecialCases(self):
        self.__parseTest("specialCasesTest.gff3")

    def testDiscontinuous(self):
        self.__parseTest("discontinuous.gff3")


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(Gff3Tests))
    return ts


if __name__ == '__main__':
    unittest.main()
