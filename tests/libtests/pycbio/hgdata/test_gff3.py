# Copyright 2006-2025 Mark Diekhans
import sys
import pickle
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.gff3 import Gff3Parser
from pycbio.sys import fileOps


def _countRows(gff3File):
    cnt = 0
    with fileOps.opengz(gff3File) as fh:
        for line in fh:
            if line[0].isalnum():
                cnt += 1
    return cnt

def _write(gff3, outGff3):
    with open(outGff3, "w") as fh:
        gff3.write(fh)

def _parseTest(request, gff3In):
    # parse and write
    gff3a = Gff3Parser().parse(gff3In)
    gff3Out1 = ts.get_test_output_file(request, ".gff3")
    _write(gff3a, gff3Out1)
    assert _countRows(gff3a.fileName) == _countRows(gff3Out1)
    ts.diff_results_expected(request, ".gff3")

    gff3b = Gff3Parser().parse(gff3In)
    gff3Out2 = ts.get_test_output_file(request, ".2.gff3")
    _write(gff3b, gff3Out2)
    ts.diff_test_files(ts.get_test_expect_file(request, ".gff3"),
                       ts.get_test_output_file(request, ".2.gff3"))
    return gff3a

def testSacCer(request):
    gff3a = _parseTest(request, ts.get_test_input_file(request, "sacCerTest.gff3"))
    #  gene	335	649
    feats = gff3a.byFeatureId["YAL069W"]
    assert len(feats) == 1
    feat = feats[0]
    # check that it is zero-based internally
    assert feat.start == 334
    assert feat.end == 649
    assert feat.getRAttr1("orf_classification") == "Dubious"

def testSpecialCases(request):
    _parseTest(request, ts.get_test_input_file(request, "specialCasesTest.gff3"))

def testDiscontinuous(request):
    _parseTest(request, ts.get_test_input_file(request, "discontinuous.gff3"))

def testPickle(request):
    gff3in = Gff3Parser().parse(ts.get_test_input_file(request, "discontinuous.gff3"))
    pickled = ts.get_test_output_file(request, ".pickle")
    with open(pickled, "wb") as fh:
        pickle.dump(gff3in, fh)
    with open(pickled, "rb") as fh:
        gff3re = pickle.load(fh)
    gff3out = ts.get_test_output_file(request, ".unpickled.gff3")
    _write(gff3re, gff3out)
    _parseTest(request, gff3out)

def testCompressed(request):
    gff3InGz = ts.get_test_output_file(request, ".tmp.gff3.gz")
    pipettor.run(("gzip", "-c", ts.get_test_input_file(request, "discontinuous.gff3")), stdout=gff3InGz)
    _parseTest(request, gff3InGz)
