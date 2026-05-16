# Copyright 2006-2025 Mark Diekhans
"""End-to-end tests for the bed-generate-parser CLI: generate a Bed subclass
from a fixture .as file, dynamically import it, parse a sample row, verify
typed fields, and verify the row round-trips through toRow()."""
import sys
import os
import os.path as osp
import importlib.util
import subprocess

if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

import pycbio.sys.testingSupport as ts


_REPO_ROOT = osp.normpath(osp.join(osp.dirname(__file__), "../../../.."))
_CLI = osp.join(_REPO_ROOT, "bin", "bed-generate-parser")


def _runGenerator(asFile, outFile):
    env = dict(os.environ)
    env["PYTHONPATH"] = osp.join(_REPO_ROOT, "lib") + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, _CLI, asFile, "-o", outFile],
                   check=True, env=env)


def _loadModule(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _genAndLoad(request, asName, className):
    asFile = ts.get_test_input_file(request, asName)
    outDir = ts.get_test_output_dir(request)
    outFile = osp.join(outDir, className + ".py")
    _runGenerator(asFile, outFile)
    return _loadModule(className, outFile)


def testBed3Generate(request):
    mod = _genAndLoad(request, "bed.as", "Bed")
    cls = mod.Bed
    row = ["chr1", "100", "200", "name1"]
    b = cls.parse(row)
    assert b.chrom == "chr1"
    assert b.chromStart == 100
    assert b.name == "name1"
    assert b.toRow() == row


def testBed8AttrsRoundTrip(request):
    mod = _genAndLoad(request, "bed8Attrs.as", "Bed8Attrs")
    row = ["chr1", "100", "200", "feat", "500", "+", "120", "180",
           "3", "a,b,c,", "x,y,z,"]
    b = mod.Bed8Attrs.parse(row)
    assert b.attrCount == 3
    assert b.attrTags == ("a", "b", "c")
    assert b.attrVals == ("x", "y", "z")
    assert isinstance(b.attrCount, int)
    assert all(isinstance(s, str) for s in b.attrTags)
    assert b.toRow() == row


def testBarChartBedFloatArrayRoundTrip(request):
    mod = _genAndLoad(request, "barChartBed.as", "BarChartBed")
    row = ["chr1", "100", "200", "gene1", "500", "+", "alt1",
           "4", "1.5,2.0,3.5,4.0,", "4096", "120"]
    b = mod.BarChartBed.parse(row)
    assert b.expCount == 4
    assert b.expScores == (1.5, 2.0, 3.5, 4.0)
    assert all(isinstance(v, float) for v in b.expScores)
    assert isinstance(b._dataOffset, int)
    assert b._dataOffset == 4096
    assert b.toRow() == row


def testBedMethylRoundTrip(request):
    mod = _genAndLoad(request, "bedMethyl.as", "BedMethyl")
    row = ["chr1", "100", "200", "site", "0", "+", "100", "200", "0",
           "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9"]
    b = mod.BedMethyl.parse(row)
    assert b.nValidCov == "v1"
    assert b.nNoCall == "v9"
    assert b.toRow() == row


def testBed12SourceRoundTrip(request):
    mod = _genAndLoad(request, "bed12Source.as", "Bed12Source")
    row = ["chr1", "100", "200", "tx", "500", "+", "110", "190", "0",
           "2", "20,30,", "0,70,", "src1"]
    b = mod.Bed12Source.parse(row)
    assert b.source == "src1"
    assert b.numStdCols == 12
    assert len(b.blocks) == 2
    assert b.toRow() == row


def testBedDetailRoundTrip(request):
    mod = _genAndLoad(request, "bedDetail.as", "BedDetail")
    row = ["chr1", "100", "200", "tx", "500", "+", "110", "190", "0",
           "2", "20,30,", "0,70,", "TX42", "a long description"]
    b = mod.BedDetail.parse(row)
    assert b.id == "TX42"
    assert b.description == "a long description"
    assert b.toRow() == row


def testBed5FloatScoreRoundTrip(request):
    mod = _genAndLoad(request, "bed5FloatScore.as", "Bed5FloatScore")
    row = ["chr1", "100", "200", "n", "750", "0.875"]
    b = mod.Bed5FloatScore.parse(row)
    assert isinstance(b.floatScore, float)
    assert b.floatScore == 0.875
    assert b.toRow() == row
