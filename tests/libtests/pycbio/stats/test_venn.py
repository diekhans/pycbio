# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.stats.venn import Venn
import pycbio.sys.testingSupport as ts

def _checkVenn(request, venn):
    with open(ts.get_test_output_file(request, ".vinfo"), "w") as viFh:
        venn.writeSets(viFh)
    with open(ts.get_test_output_file(request, ".vcnts"), "w") as viFh:
        venn.writeCounts(viFh)
    with open(ts.get_test_output_file(request, ".vmat"), "w") as viFh:
        venn.writeCountMatrix(viFh)
    ts.diff_results_expected(request, ".vinfo")
    ts.diff_results_expected(request, ".vcnts")
    ts.diff_results_expected(request, ".vmat")

def testVenn1(request):
    venn = Venn()
    venn.addItems("A", (1, 2, 3))
    venn.addItems("B", (3, 4, 5))
    venn.addItems("C", (3, 5, 6))
    _checkVenn(request, venn)

def testVenn2(request):
    venn = Venn(isInclusive=True)
    venn.addItems("A", (1, 2, 3))
    venn.addItems("B", (3, 4, 5))
    venn.addItems("C", (3, 5, 6))
    _checkVenn(request, venn)
