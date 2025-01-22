# Copyright 2006-2025 Mark Diekhans
import unittest
import sys
import pickle
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.hgdata.gff3 import Gff3Parser
from pycbio.sys import fileOps


class Gff3Tests(TestCaseBase):
    def _countRows(self, gff3File):
        cnt = 0
        with fileOps.opengz(gff3File) as fh:
            for line in fh:
                if line[0].isalnum():
                    cnt += 1
        return cnt

    def _write(self, gff3, outGff3):
        with open(outGff3, "w") as fh:
            gff3.write(fh)

    def _parseTest(self, gff3In):
        # parse and write
        gff3a = Gff3Parser().parse(gff3In)
        gff3Out1 = self.getOutputFile(".gff3")
        self._write(gff3a, gff3Out1)
        self.assertEqual(self._countRows(gff3a.fileName), self._countRows(gff3Out1))
        self.diffExpected(".gff3")

        gff3b = Gff3Parser().parse(gff3In)
        gff3Out2 = self.getOutputFile(".2.gff3")
        self._write(gff3b, gff3Out2)
        self.diffFiles(self.getExpectedFile(".gff3"), self.getOutputFile(".2.gff3"))
        return gff3a

    def testSacCer(self):
        gff3a = self._parseTest(self.getInputFile("sacCerTest.gff3"))
        #  gene	335	649
        feats = gff3a.byFeatureId["YAL069W"]
        self.assertEqual(len(feats), 1)
        feat = feats[0]
        # check that it is zero-based internally
        self.assertEqual(feat.start, 334)
        self.assertEqual(feat.end, 649)
        self.assertEqual(feat.getRAttr1("orf_classification"), "Dubious")

    def testSpecialCases(self):
        self._parseTest(self.getInputFile("specialCasesTest.gff3"))

    def testDiscontinuous(self):
        self._parseTest(self.getInputFile("discontinuous.gff3"))

    def testPickle(self):
        gff3in = Gff3Parser().parse(self.getInputFile("discontinuous.gff3"))
        pickled = self.getOutputFile(".pickle")
        with open(pickled, "wb") as fh:
            pickle.dump(gff3in, fh)
        with open(pickled, "rb") as fh:
            gff3re = pickle.load(fh)
        gff3out = self.getOutputFile(".unpickled.gff3")
        self._write(gff3re, gff3out)
        self._parseTest(gff3out)

    def testCompressed(self):
        gff3InGz = self.getOutputFile(".tmp.gff3.gz")
        pipettor.run(("gzip", "-c", self.getInputFile("discontinuous.gff3")), stdout=gff3InGz)
        self._parseTest(gff3InGz)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(Gff3Tests))
    return ts


if __name__ == '__main__':
    unittest.main()
