# Copyright 2006-2025 Mark Diekhans
import sys
import os.path as osp
import glob
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.hgbrowser import browserDir

##
# basic set of pages
##
def _genBasicData(nrows):
    "generate enough rows to create multiple pages"
    rows = []
    for i in range(nrows // 3):
        ii = i + 1
        rows.extend([
            ("chr22", ii * 1000, ii * 2000, f"fred_{i}", "sad"),
            ("chr22", ii * 1500, ii * 2300, f"barny_{i}", "happy"),
            ("chr22", ii * 3500, ii * 3700, f"wilma_{i}", "great")])
    return rows

def _basicAddRow(brDir, row):
    hrow = (brDir.mkAnchor(f"{row[0]}:{row[1]}-{row[2]}"),) + row[3:]
    rowCls = None
    if row[4] == "great":
        rowCls = "great"
    brDir.addRow(hrow, cssRowClass=rowCls)

def _basicTest(outDir):
    _basicCols = ("position", "name", "status")
    primateHub = "https://primates.org/hub.txt"
    quaryHub = "https://quary.com/hub.txt"
    css = browserDir.defaultStyle + "\n.great {background-color: aquamarine;}\n"
    brDir = browserDir.BrowserDir(browserDir.GENOME_UCSC_URL, "hg38",
                                  colNames=_basicCols,
                                  pageSize=5, style=css,
                                  title="Flintstones hub",
                                  below=True, hubUrls=[primateHub, quaryHub])
    for row in _genBasicData(15):
        _basicAddRow(brDir, row)
    brDir.write(outDir)

def _diffDir(request):
    expectHtmlFiles = sorted(glob.glob(osp.join(ts.get_test_expect_file(request), "*.html")))
    outputHtmlFiles = sorted(glob.glob(osp.join(ts.get_test_output_file(request), "*.html")))
    assert len(expectHtmlFiles) > 0
    assert len(expectHtmlFiles) == len(outputHtmlFiles)
    for expectHtmlFile, outputHtmlFile in zip(expectHtmlFiles, outputHtmlFiles):
        ts.diff_test_files(expectHtmlFile, outputHtmlFile)

def testBasic(request):
    outDir = ts.get_test_output_file(request)
    _basicTest(outDir)
    _diffDir(request)
