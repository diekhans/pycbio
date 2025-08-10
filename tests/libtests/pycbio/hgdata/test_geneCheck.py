# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.geneCheck import GeneCheckTbl

def _dumpCheck(fh, checks, g):
    g.dump(fh)
    if checks.haveDetails():
        details = checks.getDetails(g)
        if details is not None:
            for d in details:
                fh.write('\t')
                d.dump(fh)

def _checkDmp(request, checks):
    with open(ts.get_test_output_file(request, ".dmp"), 'w') as fh:
        for g in checks:
            _dumpCheck(fh, checks, g)
    ts.diff_results_expected(request, ".dmp")

def testCheck(request):
    checks = GeneCheckTbl(ts.get_test_input_file(request, "geneCheck.tsv"))
    assert len(checks) == 162
    _checkDmp(request, checks)

def testCheckDetails(request):
    checks = GeneCheckTbl(ts.get_test_input_file(request, "geneCheck.tsv"),
                          ts.get_test_input_file(request, "geneCheckDetails.tsv"))
    assert len(checks) == 162
    _checkDmp(request, checks)
