# Copyright 2006-2025 Mark Diekhans
import sys
import os.path as osp
import unittest
import glob
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

from pycbio.hgbrowser import browserDir
from pycbio.sys.testCaseBase import TestCaseBase

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

class BrowserDirTests(TestCaseBase):
    def _diffDir(self):
        expectHtmlFiles = sorted(glob.glob(osp.join(self.getExpectedFile(""), "*.html")))
        outputHtmlFiles = sorted(glob.glob(osp.join(self.getOutputFile(""), "*.html")))
        self.assertEqual(len(expectHtmlFiles), len(outputHtmlFiles))
        for i in range(len(expectHtmlFiles)):
            self.diffFiles(expectHtmlFiles[i], outputHtmlFiles[i])

    def testBasic(self):
        outDir = self.getOutputFile("")
        _basicTest(outDir)
        self._diffDir()

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(BrowserDirTests))
    return ts


if __name__ == '__main__':
    unittest.main()
