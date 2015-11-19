# Copyright 2006-2012 Mark Diekhans
import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../../..")
import re
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.gff3 import Gff3Parser

class Gff3Tests(TestCaseBase):
    def __countRows(self, gff3File):
        cnt = 0;
        with open(gff3File) as fh:
            for line in fh:
                if line[0].isalnum():
                    cnt += 1
        return cnt
        
    def __write(self, gff3, outGff3):
        with open(outGff3, "w") as fh:
            gff3.write(fh)
            
    def __check(self, gff3):
        outGff3 = self.getOutputFile(".gff3")
        self.__write(gff3, outGff3)
        self.assertEquals(self.__countRows(gff3.fileName), self.__countRows(outGff3))
        self.diffExpected(".gff3")
            
    def testSacCer(self):
        gff3 = Gff3Parser(self.getInputFile("sacCerTest.gff3")).parse()
        self.__check(gff3)

    def testSpecialCases(self):
        gff3 = Gff3Parser(self.getInputFile("specialCasesTest.gff3")).parse()
        self.__check(gff3)
        
    def testDiscontinuous(self):
        gff3 = Gff3Parser(self.getInputFile("discontinuous.gff3")).parse()
        self.__check(gff3)
        
        
def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(Gff3Tests))
    return ts

if __name__ == '__main__':
    unittest.main()
