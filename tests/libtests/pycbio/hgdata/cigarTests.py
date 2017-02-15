# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.cigar import ExonerateCigar


class CigarTests(TestCaseBase):

    def testExonerateCigars(self):
        cases = ("2354MD150M",
                 "175M4D832M52516I10M3I755M",
                 "132M3208I195M4D77M5399I238M31924I115M159I452MD267M2D288MD200M4D225M",
                 "115M",
                 "63M343I204M1378I72M1891I109M75I152M98I168M125I117M3561I78M1480I67M9974I274M2759I194M973I114M5057I76M230I83M489I125M101I133M976I81M5462I24M3278I131M621I85M4348I2254M8283I2490M",)
        for cigarStr in cases:
            cigar = ExonerateCigar(cigarStr)
            self.assertEqual(cigarStr, str(cigar))

    def testExonerateSpaceCigars(self):
        cases = (("235 4M D1 50M", "2354MD150M"),
                 ("175M 4D 832M	52516I1\n0M3I755M", "175M4D832M52516I10M3I755M"))
        for cigarStrSp, cigarStr in cases:
            cigar = ExonerateCigar(cigarStrSp)
            self.assertEqual(cigarStr, str(cigar))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CigarTests))
    return ts

if __name__ == '__main__':
    unittest.main()
