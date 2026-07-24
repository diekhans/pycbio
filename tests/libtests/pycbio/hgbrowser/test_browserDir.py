# Copyright 2006-2026 Mark Diekhans
import sys
import os.path as osp
import glob
import pytest
from pathlib import Path
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
    brDir = browserDir.BrowserDirStatic(browserDir.GENOME_UCSC_URL, "hg38",
                                        colNames=_basicCols,
                                        pageSize=5, style=css,
                                        title="Flintstones hub",
                                        doc="Characters from <b>Bedrock</b>.",
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

def testBasicPath(request):
    "outDir given as a pathlib.Path"
    outDir = Path(ts.get_test_output_file(request))
    _basicTest(outDir)
    assert osp.exists(osp.join(outDir, "index.html"))
    assert osp.exists(osp.join(outDir, "dir1.html"))

def testDeprecatedAlias():
    "BrowserDir is a deprecated alias for BrowserDirStatic"
    with pytest.warns(DeprecationWarning):
        brDir = browserDir.BrowserDir(browserDir.GENOME_UCSC_URL, "hg38")
    assert isinstance(brDir, browserDir.BrowserDirStatic)

##
# dynamic (single-page, Tabulator) directory
##
def _dynamicPosCell(brDir, chrom, start, end):
    "position cell whose sort key orders coordinates correctly"
    coords = f"{chrom}:{start}-{end}"
    sortKey = "{}\t{:012d}".format(chrom, start)
    return browserDir.Cell(coords, html=brDir.mkAnchor(coords), sortKey=sortKey)

def _dynamicAddRow(brDir, row):
    posCell = _dynamicPosCell(brDir, row[0], row[1], row[2])
    rowCls = "great" if row[4] == "great" else None
    brDir.addRow((posCell, row[3], row[4]), cssRowClass=rowCls)

def _dynamicTest(outDir):
    _cols = ("position", "name", "status")
    css = browserDir.defaultStyle + "\n.great {background-color: aquamarine;}\n"
    brDir = browserDir.BrowserDirDynamic(browserDir.GENOME_UCSC_URL, "hg38",
                                         colNames=_cols, style=css,
                                         title="Flintstones hub", below=True,
                                         colDefs={"name": {"width": 120, "wrap": True}})
    for row in _genBasicData(15):
        _dynamicAddRow(brDir, row)
    brDir.write(outDir)

def testDynamic(request):
    outDir = ts.get_test_output_file(request)
    _dynamicTest(outDir)
    assert osp.exists(osp.join(outDir, "index.html"))
    assert osp.exists(osp.join(outDir, "dir.html"))
    _diffDir(request)


##
# dynamic directory with genomic sort keys, a fixed-width wrapping column,
# and row shading (mirrors realistic multi-chromosome usage)
##
_genesCols = ("position", "gene", "description", "length", "status")

# (chrom, start, end, symbol, description, status)
_genesData = (
    ("chr17", 43044295, 43125483, "BRCA1", "DNA repair; breast/ovarian cancer susceptibility", "done"),
    ("chr7", 55019017, 55211628, "EGFR", "epidermal growth factor receptor; amplified in tumors", "done"),
    ("chr8", 127735434, 127742951, "MYC", "MYC proto-oncogene, bHLH transcription factor", "review"),
    ("chr13", 32315086, 32400268, "BRCA2", "DNA repair; Fanconi anemia complementation group", "review"),
    ("chr10", 87863625, 87971930, "PTEN", "phosphatase and tensin homolog; tumor suppressor", "todo"),
    ("chr2", 47403067, 47634501, "MSH2", "mutS homolog 2; Lynch syndrome mismatch repair", "todo"))

def _genesPosCell(brDir, chrom, start, end):
    "position cell with a genomic sort key (chr2 sorts before chr10)"
    coords = f"{chrom}:{start + 1}-{end}"
    sortKey = "{}\t{:012d}".format(chrom[3:].zfill(3), start)
    return browserDir.Cell(coords, html=brDir.mkAnchor(coords), sortKey=sortKey)

def _genesLenCell(start, end):
    "numeric length cell: comma-formatted display, numeric sort/range key"
    length = end - start
    return browserDir.Cell(f"{length:,}", sortKey=length)

def _genesAddRow(brDir, gene):
    chrom, start, end, symbol, desc, status = gene
    rowCls = "great" if status == "done" else None
    posCell = _genesPosCell(brDir, chrom, start, end)
    lenCell = _genesLenCell(start, end)
    brDir.addRow((posCell, symbol, desc, lenCell, status), cssRowClass=rowCls)

def _genesTest(outDir):
    css = browserDir.defaultStyle + "\n.great {background-color: #d7f0d7;}\n"
    brDir = browserDir.BrowserDirDynamic(browserDir.GENOME_UCSC_URL, "hg38",
                                         colNames=_genesCols, style=css,
                                         title="hg38 genes", dirPercent=45,
                                         colDefs={"position": {"minWidth": 230},
                                                  "gene": {"fit": True},
                                                  "description": {"wrap": True,
                                                                  "headerWrap": True},
                                                  "length": {"filter": "range"}})
    for gene in _genesData:
        _genesAddRow(brDir, gene)
    brDir.write(outDir)

def testDynamicGenes(request):
    outDir = ts.get_test_output_file(request)
    _genesTest(outDir)
    assert osp.exists(osp.join(outDir, "index.html"))
    assert osp.exists(osp.join(outDir, "dir.html"))
    _diffDir(request)


##
# per-assembly miRNA gene table (mirrors hub-geneset-browser): one row per
# merged locus, all loci of a gene share the copies count; numeric copies
# column with a range filter; location columns are HTML anchors whose text
# (the position) sorts/filters/fits; GRCh38 location empty when no ref locus
##
_mirnaAssembly = "GCA_018852605.1"
_mirnaCols = ("gene", "family", "gene_id", "copies", "conflict",
              "assembly location", "GRCh38 location")

# (gene, family, gene_id, copies, conflict, assembly_pos, grch38_pos or None)
_mirnaData = (
    ("Hsa-Mir-21", "MIR-21", "ENSG00000284190", 1, "no", "chr17:59841266-59841337", "chr17:59841266-59841337"),
    ("Hsa-Mir-10a", "MIR-10", "ENSG00000284420", 2, "no", "chr17:48632267-48632377", "chr17:48632267-48632377"),
    ("Hsa-Mir-10a", "MIR-10", "ENSG00000284420", 2, "gene", "chr17:48640001-48640110", "chr17:48632267-48632377"),
    ("Hsa-Mir-10b", "MIR-10", "ENSG00000207996", 1, "gene", "chr2:176155838-176155948", "chr2:176155838-176155948"),
    ("Hsa-Let-7a-1", "LET-7", "ENSG00000199165", 3, "no", "chr9:94175957-94176036", "chr9:94175957-94176036"),
    ("Hsa-Let-7a-1", "LET-7", "ENSG00000199165", 3, "family", "chr9:94180500-94180579", "chr9:94175957-94176036"),
    ("Hsa-Let-7a-1", "LET-7", "ENSG00000199165", 3, "family", "chr9:94190100-94190179", "chr9:94175957-94176036"),
    ("Hsa-Mir-451a", "MIR-451", "ENSG00000284567", 1, "no", "chr17:28861371-28861442", "chr17:28861371-28861442"),
    ("Hsa-Mir-127", "MIR-127", "Mir-127", 1, "no", "chr14:100882979-100883075", None),
    ("Hsa-Mir-9-1", "MIR-9", "ENSG00000207828", 5, "gene", "chr1:156390133-156390221", "chr1:156390133-156390221"),
    ("Hsa-Mir-9-1", "MIR-9", "ENSG00000207828", 5, "no", "chr1:156400000-156400088", "chr1:156390133-156390221"),
    ("Hsa-Mir-9-1", "MIR-9", "ENSG00000207828", 5, "family", "chr1:156410000-156410088", "chr1:156390133-156390221"),
    ("Hsa-Mir-1246", "MIR-1246", "Mir-1246", 8, "family", "chr2:176100050-176100160", None),
    ("Hsa-Mir-1246", "MIR-1246", "Mir-1246", 8, "family", "chr2:176120050-176120160", None),
    ("Hsa-Mir-3648", "MIR-3648", "ENSG00000271528", 2, "no", "chr21:8205348-8205422", "chr21:8205348-8205422"))

def _mirnaAddRow(brDir, rec):
    gene, family, geneId, copies, conflict, asmPos, refPos = rec
    asmCell = brDir.mkAnchor(asmPos)
    refCell = brDir.mkAnchor(refPos, db="hg38") if refPos else ""
    row = (gene, family, geneId, browserDir.Cell(copies), conflict, asmCell, refCell)
    brDir.addRow(row)

def _mirnaTest(outDir):
    doc = ["One row per merged miRNA locus; all loci of a gene share the same"
           " <b>copies</b> count.",
           "<b>conflict</b> is <tt>no</tt>, <tt>gene</tt>, or <tt>family</tt>."]
    brDir = browserDir.BrowserDirDynamic(browserDir.GENOME_UCSC_URL, _mirnaAssembly,
                                         colNames=_mirnaCols, dirPercent=100, doc=doc,
                                         title="miRNA loci ({})".format(_mirnaAssembly),
                                         colDefs={"copies": {"filter": "range"},
                                                  "assembly location": {"expand": True},
                                                  "GRCh38 location": {"expand": True}})
    for rec in _mirnaData:
        _mirnaAddRow(brDir, rec)
    brDir.write(outDir)

def testDynamicMirna(request):
    outDir = ts.get_test_output_file(request)
    _mirnaTest(outDir)
    assert osp.exists(osp.join(outDir, "index.html"))
    assert osp.exists(osp.join(outDir, "dir.html"))
    _diffDir(request)
