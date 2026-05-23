# pycbio Library Usage Guide

This skill helps you work with the pycbio computational biology library.

## Library Overview

pycbio is Mark Diekhans's Python 3 library for computational biology and bioinformatics, focused on UCSC Browser data formats.

## Core Modules

### Command Line Parsing (`pycbio.sys.cli`)

The cli module provides argparse helpers with integrated logging and error handling.

**Standard program structure:**

```python
import argparse
from pycbio.sys import cli

def parse_args():
    parser = argparse.ArgumentParser(description="My tool")
    parser.add_argument("inFile")
    parser.add_argument("outFile")
    parser.add_argument("--threshold", type=float, default=0.5)
    return cli.parseOptsArgsWithLogging(parser)

def my_tool(opts, in_file, out_file):
    """Main logic here"""
    process(in_file, out_file, opts.threshold)

def main():
    opts, args = parse_args()
    with cli.ErrorHandler():
        my_tool(opts, args.inFile, args.outFile)

main()
```

**Key functions:**
- `cli.parseOptsArgsWithLogging(parser)` - Returns `(opts, args)` as ObjDict objects with logging setup
- `cli.parseOptsArgs(parser)` - Returns `(opts, args)` without logging setup
- `cli.ErrorHandler()` - Context manager that catches exceptions, logs them, and exits non-zero

**Automatic logging options added:**
- `--log-level LEVEL` - Set log level (DEBUG, INFO, WARNING, ERROR)
- `--log-debug` - Shortcut for `--log-stderr --log-level=DEBUG`
- `--log-stderr` - Log to stderr
- `--log-conf FILE` - Python logging config file

**ErrorHandler behavior:**
- Catches all exceptions and logs them
- Exits with code 1 on error
- Shows stack traces only when `--log-debug` is set
- Suppresses stack for `OSError`, `ImportError`, `KeyboardInterrupt` by default

**Raising CLI errors:**

```python
from pycbio.sys.cli import CliError

if not valid_input:
    raise CliError("Invalid input format")  # No stack trace printed
```

### TSV File Handling (`pycbio.tsv`)

```python
from pycbio.tsv import TsvReader, TsvWriter

# Read TSV with automatic type conversion
for row in TsvReader("data.tsv", typeMap={"score": int, "pValue": float}):
    print(row.name, row.score)

# Write TSV with schema
with TsvWriter("output.tsv", columns=("name", "score", "strand")) as writer:
    writer.writeRow(name="gene1", score=100, strand="+")
```

### BED Format (`pycbio.hgdata.bed`)

```python
from pycbio.hgdata.bed import Bed, BedReader

# Read BED file
for bed in BedReader("genes.bed"):
    print(bed.chrom, bed.chromStart, bed.chromEnd, bed.name)

# Create BED object
bed = Bed(chrom="chr1", chromStart=1000, chromEnd=2000, name="feature1")
```

### GenePred Format (`pycbio.hgdata.genePred`)

```python
from pycbio.hgdata.genePred import GenePredReader

# Read gene predictions
for gp in GenePredReader("genes.gp"):
    print(gp.name, gp.chrom, gp.txStart, gp.txEnd)
    for exon in gp.exons:
        print(f"  exon: {exon.start}-{exon.end}")
```

### PSL Alignments (`pycbio.hgdata.psl`)

```python
from pycbio.hgdata.psl import PslReader

# Read PSL alignments
for psl in PslReader("alignments.psl"):
    print(psl.qName, psl.tName, psl.tStart, psl.tEnd)
    print(f"  identity: {psl.identity():.2%}")
```

### GFF3 Format (`pycbio.hgdata.gff3`)

```python
from pycbio.hgdata.gff3 import Gff3Parser

# Parse GFF3 file
parser = Gff3Parser("annotations.gff3")
for feature in parser.parse():
    print(feature.seqid, feature.type, feature.start, feature.end)
```

### Coordinates (`pycbio.hgdata.coords`)

```python
from pycbio.hgdata.coords import Coords

# Create coordinate object (0-based, half-open)
coord = Coords(name="chr1", start=1000, end=2000, strand="+", size=249250621)

# Reverse complement
rev_coord = coord.reverse()
```

### File Operations (`pycbio.sys.fileOps`)

```python
from pycbio.sys.fileOps import opengz, iterLines, ensureDir, atomicTmpFile

# Read compressed files transparently
with opengz("data.tsv.gz") as fh:
    for line in fh:
        process(line)

# Atomic file writing
with atomicTmpFile("output.tsv") as tmpPath:
    # Write to tmpPath, automatically renamed on success
    pass
```

### Database Operations (`pycbio.db.sqliteOps`)

```python
from pycbio.db.sqliteOps import connect, SqliteTable

# Connect to SQLite database
conn = connect("data.db")

# Query with object dict rows
for row in conn.execute("SELECT * FROM genes"):
    print(row.name, row.chrom)
```

### NCBI Assembly Reports (`pycbio.ncbi.assembly`)

```python
from pycbio.ncbi.assembly import AssemblyReport

# Parse NCBI assembly report
report = AssemblyReport("GCF_000001405.40_GRCh38.p14_assembly_report.txt")
for rec in report.records:
    print(rec.sequenceName, rec.genbankAccn, rec.refseqAccn)
```

### Range Finding (`pycbio.hgdata.rangeFinder`)

```python
from pycbio.hgdata.rangeFinder import RangeFinder

# Efficient overlap queries
finder = RangeFinder()
finder.add("chr1", 1000, 2000, "feature1")
finder.add("chr1", 1500, 2500, "feature2")

# Find overlaps
for entry in finder.overlapping("chr1", 1200, 1800):
    print(entry.value)
```

## Command-Line Tools

The library includes these CLI tools in `bin/`:

- `bedToCdsBed` - Convert BED to CDS BED format
- `bedFlatten` - Flatten overlapping BED entries
- `bedToIntronBed` - Extract introns from BED
- `agpToPsl` - Convert AGP to PSL
- `csv-to-tsv` - Convert CSV to TSV
- `gbffGenesToGenePred` - GenBank to GenePred
- `genePredSelect` - Filter gene predictions
- `ncbiAssemblyReportConvert` - Convert NCBI assembly reports
- `vennChart` - Generate Venn diagrams

## Key Design Patterns

1. **Zero-based, half-open coordinates** - All genomic coordinates use this convention
2. **Strand-aware operations** - Proper handling of + and - strands
3. **Transparent compression** - .gz and .bz2 files handled automatically
4. **Type conversion maps** - Schema-driven TSV reading with automatic type conversion

## When Assisting with pycbio

1. Use 0-based, half-open coordinates consistently
2. Prefer the library's readers/writers over manual parsing
3. Use `opengz()` for transparent compression handling
4. Follow PEP-8 style with double-quoted strings
5. Run tests with `python -m pytest tests/`