# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.sys.fileOps import prRowv
from pycbio.align.pairAlign import loadPslFile
from pycbio import PycbioException


class WithSrcCds:
    "container for map CDS results"
    def __init__(self, srcAln, destAln):
        self.srcAln = srcAln
        self.destAln = destAln

    def dump(self, fh):
        prRowv(fh, "srcQCds: ", self.srcAln.qSeq)
        prRowv(fh, "srcTCds: ", self.srcAln.tSeq)
        self.destAln.dump(fh)


def _dumpNDiff(request, alns, suffix):
    with open(ts.get_test_output_file(request, suffix), "w") as fh:
        for pa in alns:
            pa.dump(fh)
    ts.diff_results_expected(request, suffix)

def testLoad(request):
    alns = loadPslFile(ts.get_test_input_file(request, "hsRefSeq.psl"),
                       ts.get_test_input_file(request, "hsRefSeq.cds"))
    _dumpNDiff(request, alns, ".out")

def testRevCmpl(request):
    alns = loadPslFile(ts.get_test_input_file(request, "hsRefSeq.psl"),
                       ts.get_test_input_file(request, "hsRefSeq.cds"))
    ralns = []
    rralns = []
    for pa in alns:
        rpa = pa.revCmpl()
        ralns.append(rpa)
        rralns.append(rpa.revCmpl())
    _dumpNDiff(request, ralns, ".rout")
    _dumpNDiff(request, rralns, ".rrout")

def testLoadUnaln(request):
    alns = loadPslFile(ts.get_test_input_file(request, "hsRefSeq.psl"),
                       ts.get_test_input_file(request, "hsRefSeq.cds"),
                       inclUnaln=True)
    _dumpNDiff(request, alns, ".out")

def doTestProjectCds(request, contained):
    alns = loadPslFile(ts.get_test_input_file(request, "refseqWeird.psl"),
                       ts.get_test_input_file(request, "refseqWeird.cds"),
                       inclUnaln=True)
    qalns = []
    for pa in alns:
        pa.projectCdsToTarget(contained=contained)
        # project back
        qpa = pa.copy()
        qpa.qSubSeqs.clearCds()
        qpa.projectCdsToQuery(contained=contained)
        qalns.append(qpa)
    _dumpNDiff(request, alns, ".tout")
    _dumpNDiff(request, qalns, ".qout")

def testProjectCds(request):
    doTestProjectCds(request, False)

def testProjectCdsContained(request):
    doTestProjectCds(request, True)

def doTestMapCds(request, contained):
    destAlns = loadPslFile(ts.get_test_input_file(request, "clonesWeird.psl"),
                           inclUnaln=True)
    srcAlns = loadPslFile(ts.get_test_input_file(request, "refseqWeird.psl"),
                          ts.get_test_input_file(request, "refseqWeird.cds"),
                          inclUnaln=True,
                          projectCds=True)
    mappedAlns = []
    for destAln in destAlns:
        for srcAln in srcAlns:
            if srcAln.qSeq.cds is None:
                raise PycbioException("no qCDS: " + srcAln.qSeq.id + " <=> " + srcAln.tSeq.id)
            if srcAln.tSeq.cds is None:
                raise PycbioException("no tCDS: " + srcAln.qSeq.id + " <=> " + srcAln.tSeq.id)
            if srcAln.targetOverlap(destAln):
                ma = destAln.copy()
                ma.mapCds(srcAln, srcAln.tSeq, ma.tSeq, contained=contained)
                mappedAlns.append(WithSrcCds(srcAln, ma))
    _dumpNDiff(request, mappedAlns, ".out")

def testMapCds(request):
    doTestMapCds(request, contained=False)

def testMapCdsContained(request):
    doTestMapCds(request, contained=True)
