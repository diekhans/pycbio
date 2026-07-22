---
name: pycbio
description: Conventions and API for writing Python tools with markd's pycbio library — TSV I/O (TsvReader/TsvWriter, attribute-access rows), atomic file writes (fileOps), CLI arg parsing + error handling (sys.cli), and SymEnum. Use whenever creating or editing a Python script that reads/writes TSVs or follows the pycbio tool style.
---

# Writing tools with pycbio

`pycbio` is markd's Python library (on `PYTHONPATH` via each project's `lib/`).
This skill captures the house style for command-line tools built on it. Prefer
these over hand-rolled `csv`, `open()`, or `argparse.parse_args()`.

## Golden rules

- **TSV rows are field-addressable objects, never dicts.** Access columns as
  attributes: `row.gene`, `row.num_loci` — **never** `row["gene"]`. A `["..."]`
  on a TSV row is a bug; string-indexing means the value is a `Counter`/`dict`,
  not a `TsvRow`.
- **Write output atomically.** Never write a final path directly; use
  `fileOps.AtomicFileCreate` / `AtomicFileOpen` so a crash can't leave a
  half-written file. `ensureFileDir(path)` first.
- **Parse args with `cli.parseOptsArgsWithLogging`** and run the body inside a
  `cli.ErrorHandler`.
- **Never use pandas.** All tabular work goes through `TsvReader`/`TsvWriter`.

## Reading TSVs — `TsvReader`

```python
from pycbio.tsv import TsvReader

for row in TsvReader(path):
    use(row.gene, row.num_loci)      # attribute access; values are str by default

reader = TsvReader(path)
reader.columns                       # list of header column names
rows = list(TsvReader(path))         # materialize when you need >1 pass
```

Signature (keyword-only options):
`TsvReader(fileName, *, rowClass=None, typeMap=None, defaultColType=None, columns=None, columnNameMapper=None, ignoreExtraCols=False, ...)`

- Values are **strings** unless typed. To coerce:
  - `typeMap={"num_loci": int, "gc_per": float}` — per-column converters.
  - `defaultColType=int` — convert every column the same way.
- `columns=[...]` supplies names for a headerless file.
- `rowClass=` — a `TsvRow` subclass to get computed properties (see below).

## Typed, behavior-carrying rows — subclass `TsvRow`

Wrap a catalog so derived values live on the row, not scattered in callers
(this project's `config.Assembly` does exactly this):

```python
from pycbio.tsv import TsvReader, TsvRow

class Assembly(TsvRow):
    @property
    def genome_fasta(self):
        return GENOME_DIR / f"{self.ncbi_assembly}.fa"

def load():
    return list(TsvReader(ASSEMBLIES_TSV, rowClass=Assembly))
```

Rule of thumb: **derive paths/values as `@property` on the row class**; callers
never rebuild them.

## Writing TSVs — `TsvWriter`

```python
from pycbio.sys import fileOps
from pycbio.tsv import TsvWriter

COLUMNS = ("gene", "family", "num_loci")

def write(rows, out_tsv):
    fileOps.ensureFileDir(out_tsv)
    with TsvWriter(out_tsv, columns=COLUMNS) as tw:
        for r in rows:
            tw.writeColumns(gene=r.gene, family=r.family, num_loci=r.count)
```

- `TsvWriter(fileName, *, columns=None, typeMap=None, writeHeader=True, ...)`.
- `tw.writeColumns(**kwargs)` — keys must match `columns`; order is fixed by
  `columns`, so callers pass by name. Also `writeRow(seq)` / `writeRows(iter)`.
- `TsvWriter` is a context manager — the `with` closes it. For atomic output,
  point it at a temp path (see next section) or rely on the fact that callers
  usually write to the final path only after all rows are computed.

## Atomic file output — `fileOps`

```python
from pycbio.sys import fileOps

fileOps.ensureFileDir(path)                     # mkdir -p of the parent

with fileOps.AtomicFileCreate(path) as tmp:     # yields a temp path in the same dir
    write_something(tmp)                        # ...installed to `path` only on clean exit

with fileOps.AtomicFileOpen(path) as fh:        # same, but yields an open file handle
    fh.write(text)

for line in fileOps.iterLines(path):            # newline-stripped lines; handles .gz
    ...
```

`AtomicFileCreate` writes to a sibling temp file and renames on success, so
readers never see a partial file and a failed run leaves the old output intact.
Combine with a `.done` sentinel for idempotent stages.

## CLI tools — `sys.cli`

House layout for an executable tool (bare top-level, ends with a `main()` call;
put `import argparse` at the top for non-library scripts):

```python
#!/usr/bin/env python3
"""One-line description, then details."""
import argparse
from pycbio.sys import cli

def parse_args():
    parser = argparse.ArgumentParser(description="what it does")
    parser.add_argument("--perc-identity", type=int, default=95)
    parser.add_argument("in_tsv")
    parser.add_argument("out_tsv")
    opts, args = cli.parseOptsArgsWithLogging(parser)   # returns (opts, args)
    if opts.perc_identity > 100:
        parser.error("--perc-identity must be <= 100")   # validate here
    return opts, args

def the_tool(opts, args):
    ...

def main():
    opts, args = parse_args()
    with cli.ErrorHandler(noStackExcepts=(OSError, ImportError, cli.PycbioException)):
        the_tool(opts, args)

main()
```

- `parseOptsArgsWithLogging(parser)` adds standard logging flags and returns
  `(opts, args)` — by convention `opts` holds the `--flags`, `args` the
  positionals (argparse puts both on one namespace; the pair is split for
  readability).
- `cli.ErrorHandler(noStackExcepts=(...))` prints a clean message (no traceback)
  for the listed exception types; anything else gets a full stack. Raise
  `cli.PycbioException` for expected user-facing errors.
- Validate arguments in `parse_args` with `parser.error(...)`.

## Enums — `SymEnum`

Symbolic enum whose members compare/serialize by name (good for a TSV column's
allowed values):

```python
from pycbio.sys.symEnum import SymEnum

class AssemblyType(SymEnum):
    hprc = 1
    other = 2
```

## Running subprocesses — `pipettor` (companion lib)

Not part of pycbio, but the standard pairing. Commands are **lists**, pipelines
are **lists of lists**; send stderr to the parent:

```python
import pipettor
pipettor.run(["makeblastdb", "-in", fa, "-dbtype", "nucl"], stderr=2)
pipettor.run([["blastn", "-query", q, "-outfmt", "5"],
              ["blastXmlToPsl", "stdin", psl]], stderr=2)
```

## Quick checklist for a new tool

- [ ] `TsvReader` for input; access rows by attribute, not `[...]`.
- [ ] `TsvWriter(out, columns=...)` + `writeColumns(**)` for output.
- [ ] `ensureFileDir` + `AtomicFileCreate`/`AtomicFileOpen` for every written file.
- [ ] `parseOptsArgsWithLogging` + `ErrorHandler`; validate with `parser.error`.
- [ ] Idempotent: skip when output (or a `.done`) already exists.
- [ ] No pandas; no `csv`; no bare `open()` for final outputs.
