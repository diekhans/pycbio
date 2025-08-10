# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.clusterGenes import ClusterGenes


def testLoad(request):
    clusters = ClusterGenes(ts.get_test_input_file(request, "models.loci"))

    clCnt = 0
    geneCnt = 0
    for cl in clusters:
        clCnt += 1
        for g in cl:
            geneCnt += 1
    assert clCnt == 16
    assert geneCnt == 49

    # try getting gene, and go back to it's cluster
    assert len(clusters.genes["NR_046018.2"]) == 1
    g = clusters.genes["ENST00000335137.4"][0]
    cl = g.clusterObj
    assert len(cl) == 3
    assert frozenset([g.gene for g in cl]) == frozenset(["ENST00000335137.4", "NM_001005484.1", "ENST00000641515.2"])
