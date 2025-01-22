# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
import pysam
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.cigar import cigarStringParse, cigarFromPysam


class CigarTests(TestCaseBase):

    def testCigars(self):
        cases = ("2354MD150M",
                 "175M4D832M52516I10M3I755M",
                 "132M3208I195M4D77M5399I238M31924I115M159I452MD267M2D288MD200M4D225M",
                 "115M",
                 "63M343I204M1378I72M1891I109M75I152M98I168M125I117M3561I78M1480I67M9974I274M2759I194M973I114M5057I76M230I83M489I125M101I133M976I81M5462I24M3278I131M621I85M4348I2254M8283I2490M",)
        for cigarStr in cases:
            cigar = cigarStringParse(cigarStr)
            self.assertEqual(cigarStr, str(cigar))

    def testExonerateSpaceCigars(self):
        cases = (("235 4M D1 50M", "2354MD150M"),
                 ("175M 4D 832M	52516I1\n0M3I755M", "175M4D832M52516I10M3I755M"))
        for cigarStrSp, cigarStr in cases:
            cigar = cigarStringParse(cigarStrSp)
            self.assertEqual(cigarStr, str(cigar))

    def testMinimapCigar(self):
        # minimap2, ONT RNA-Seq
        cases = (
            "485S133M1D22M2D9M1D139M11S",
            "326S87M1D4M4I6M1I20M1D1M1D185M1I91M1I68M140N61M1I4M2I4M757N108M1I44M659N37M1D6M1I34M1I46M1I4M1D11M1I2M1D16M92N20M31S",
            "88S52M5I33M1D80M1I1M1I30M1I97M1D58M2I17M1D5M1D6M1I3M4D36M140N2M1I51M2I16M757N8M2I11M1D22M1I4M1I2M2D24M3D18M1I8M1D4M1I44M659N140M1I1M1I10M1D7M88N56M1D7M2D13M1D7M2D37M3I13M1D43M1I2M1D16M177N100M1D5M1D29M237N116M1D7M1D12M172N29M52S",
            "76S52M5I138M1D109M1D54M2D1M1I57M1D10M140N69M757N71M1D2M1D33M1I13M1I1M1I5M2D23M659N8M2I2M1I149M88N37M1I165M177N136M237N85M2I52M172N50M2D15M1128S",
        )
        for cigarStr in cases:
            cigar = cigarStringParse(cigarStr)
            self.assertEqual(cigarStr, cigar.format(inclOnes=True))

    def testPysamToCigar(self):
        with (pysam.AlignmentFile(self.getInputFile("ont-rna.sam"), "r") as samfh,
              open(self.getOutputFile(".cigar"), 'w') as cigarfh):
            for aln in samfh:
                cigar = cigarFromPysam(aln.cigartuples)
                print(str(cigar), file=cigarfh)
        self.diffExpected(".cigar")


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CigarTests))
    return ts


if __name__ == '__main__':
    unittest.main()
