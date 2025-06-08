# Copyright 2006-2025 Mark Diekhans
import os
import sys
import shutil
import re
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys import testSupport as ts
from pycbio.sys import fileOps
import pipettor


def testOpengzReadPlain(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    with fileOps.opengz(inf) as inFh, open(outf, "w") as outFh:
        shutil.copyfileobj(inFh, outFh)
    ts.diff_test_files(inf, outf)

def testOpengzWritePlain(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    with open(inf) as inFh, fileOps.opengz(outf, "w") as outFh:
        shutil.copyfileobj(inFh, outFh)
    ts.diff_test_files(inf, outf)

def testOpengzReadGz(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    infGz = ts.get_test_output_file(request, ".out.gz")
    pipettor.run(("gzip", "-c", inf), stdout=infGz)
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    with fileOps.opengz(infGz) as inFh, open(outf, "w") as outFh:
        shutil.copyfileobj(inFh, outFh)
    ts.diff_test_files(inf, outf)

def testOpengzWriteGz(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    outfGz = ts.get_test_output_file(request, ".out.gz")
    fileOps.rmFiles(outf, outfGz)
    with open(inf) as inFh, fileOps.opengz(outfGz, "w") as outFh:
        shutil.copyfileobj(inFh, outFh)
    pipettor.run(("gunzip", "-c", outfGz), stdout=outf)
    ts.diff_test_files(inf, outf)

def testOpengzReadBz2(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    infBz2 = ts.get_test_output_file(request, ".out.bz2")
    pipettor.run(("bzip2", "-c", inf), stdout=infBz2)
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    with fileOps.opengz(infBz2) as inFh, open(outf, "w") as outFh:
        shutil.copyfileobj(inFh, outFh)
    ts.diff_test_files(inf, outf)

def testOpengzWriteBz2(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    outfBz2 = ts.get_test_output_file(request, ".out.bz2")
    fileOps.rmFiles(outf, outfBz2)
    with open(inf) as inFh, fileOps.opengz(outfBz2, "w") as outFh:
        shutil.copyfileobj(inFh, outFh)
    pipettor.run(("bunzip2", "-c", outfBz2), stdout=outf)
    ts.diff_test_files(inf, outf)

def testOpengzWriteBgzip(request):
    # gzip is special
    inf = ts.get_test_input_file(request, "simple1.txt")
    outfGz = ts.get_test_output_file(request, ".out.gz")
    fileOps.rmFiles(outfGz)
    with open(inf) as inFh, fileOps.opengz(outfGz, "w", bgzip=True) as outFh:
        shutil.copyfileobj(inFh, outFh)
    info = pipettor.runout(['file', outfGz])

    # MacOS: gzip compressed data, extra field, original size modulo 2^32 0
    # newer GNU: Blocked GNU Zip Format (BGZF; gzip compatible), block length 16437
    # older GNU: gzip compressed data, extra field
    assert re.search(r".*(extra field)|(BGZF).*", info)

def testAtomicInstall(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    outfTmp = fileOps.atomicTmpFile(outf)
    shutil.copyfile(inf, outfTmp)
    fileOps.atomicInstall(outfTmp, outf)
    ts.diff_test_files(inf, outf)

def testAtomicInstallDev(request):
    devn = '/dev/null'
    tmp = fileOps.atomicTmpFile(devn)
    assert tmp == devn
    fileOps.atomicInstall(tmp, devn)

def testAtomicContextOk(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    with fileOps.AtomicFileCreate(outf) as outfTmp:
        shutil.copyfile(inf, outfTmp)
    ts.diff_test_files(inf, outf)

def testAtomicContextError(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    try:
        with fileOps.AtomicFileCreate(outf) as outfTmp:
            shutil.copyfile(inf, outfTmp)
            raise Exception("stop!")
    except Exception as ex:
        assert str(ex) == "stop!"
    assert not os.path.exists(outf)

def testAtomicContextNoOutError(request):
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    try:
        with fileOps.AtomicFileCreate(outf):
            raise Exception("stop!")
    except Exception as ex:
        assert str(ex) == "stop!"
    assert not os.path.exists(outf)

def testAtomicOpenOk(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    with fileOps.AtomicFileOpen(outf) as outfh:
        with open(inf) as infh:
            shutil.copyfileobj(infh, outfh)
    ts.diff_test_files(inf, outf)

def testAtomicOpenError(request):
    inf = ts.get_test_input_file(request, "simple1.txt")
    outf = ts.get_test_output_file(request, ".out")
    fileOps.rmFiles(outf)
    try:
        with fileOps.AtomicFileOpen(outf) as outfh:
            with open(inf) as infh:
                shutil.copyfileobj(infh, outfh)
            raise Exception("stop!")
    except Exception as ex:
        assert str(ex) == "stop!"
    assert not os.path.exists(outf)


simple1Lines = ['one', 'two', 'three', 'four', 'five', 'six']

def testReadFileLines(request):
    lines = fileOps.readFileLines(ts.get_test_input_file(request, "simple1.txt"))
    assert simple1Lines == lines

def testReadNonCommentLines(request):
    lines = fileOps.readNonCommentLines(ts.get_test_input_file(request, "comments1.txt"))
    assert simple1Lines == lines

def testIterLineName(request):
    lines = [l for l in fileOps.iterLines(ts.get_test_input_file(request, "simple1.txt"))]
    assert simple1Lines == lines

def testIterLineFh(request):
    with open(ts.get_test_input_file(request, "simple1.txt")) as fh:
        lines = [l for l in fileOps.iterLines(fh)]
    assert simple1Lines == lines

def testMd5Sum(request):
    md5 = fileOps.md5sum(ts.get_test_input_file(request, "simple1.txt"))
    assert 'b256e7fa23f105539085c7c895557c41' == md5

def testMd5Sums(request):
    expected = [("simple1.txt", "b256e7fa23f105539085c7c895557c41"),
                ("comments1.txt", "4179a04267de41833d87e182b22999ca")]
    got = fileOps.md5sums([ts.get_test_input_file(request, f[0]) for f in expected])
    assert len(expected) == len(got)
    for e, g in zip(expected, got):
        assert e[0] == os.path.basename(g[0])
        assert e[1] == g[1]


# FIXME: many more tests needed
