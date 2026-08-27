# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Mark Diekhans's personal Python 3 library and command-line tools for computational biology,
geared to UCSC Genome Browser data.  No formal release process; API compatibility may be
broken at will.  Library lives in `lib/pycbio`, installable scripts in `bin/`.

This library is used by a lot of code outside this repository: project trees, analysis
scripts, and pipelines that are not checked in here.  Consequences for any change:

- A grep of this repository cannot show whether a function, class, or module has callers.
  No in-repo user is not evidence that something is unused.
- Never propose removing or renaming public API on the strength of an in-repo search.  Ask,
  or state plainly that only this repo was searched.
- Deletions and signature changes are the expensive kind of change here, since the breakage
  shows up in another tree at run time.  Additions and internal fixes are cheap.

`skills/pycbio/SKILL.md` is the house style for writing tools on this library (TSV I/O,
atomic writes, `cli` arg parsing, SymEnum, snakemake stages).  Read it before writing or
editing a script that uses pycbio.

## Commands

All make targets pick up `defs.mk`, which puts `lib` on `PYTHONPATH` and sets
`PYTHONWARNINGS=always`.

- `make` - byte-compile the library (`compileall`), the only "build".
- `make test` - libtests plus progtests.
- `make libtest` / `make progtest` - one regime only.
- `make test-full` - adds the slow progtests (`sra`, hits the network).
- `make lint` - flake8 over `lib/pycbio`, `tests/libtests`, and the Python scripts in
  `bin/` and `tests/bin`.  Config in `setup.cfg`: max-line-length 500, max-complexity 14.
- `make clean` - removes `output/` dirs, `common-output`, `*.pyc`, build products.

Single pytest test, through make (xdist parallelism off so stdout is visible):

```
cd tests && make libtest nproc=0 pytest_extra="-k tsvReader"
```

Or directly, which requires both paths since there is no conftest.py or pytest config:

```
cd tests && PYTHONPATH=../lib:libtests pytest -q libtests/pycbio/tsv/test_tsvReader.py
```

Single progtest: `cd tests/progtests/<dir> && make test`, or one target inside that
Makefile by name.

`tests/Makefile` builds `tests/common-output` (bgzip + faidx + 2bit of
`tests/data/grch38-regions.fa`) before libtests; that needs `samtools`, `bgzip`, and
`faToTwoBit` on `PATH`.  Tests needing a UCSC browser MySQL database skip themselves
unless running on `hgwdev` with `~/.hg.conf` and `mysqlclient` installed
(`tests/libtests/testlib/mysqlCheck.py`).

## Two test regimes

- `tests/libtests/pycbio/<package>/test_*.py` - pytest, mirroring the library tree.
  Data-driven tests write into a per-directory `output/` and diff against `expected/`
  using `pycbio.sys.testingSupport` (imported as `ts`): take pytest's `request` fixture
  and call `ts.get_test_input_file(request, name)`, `ts.get_test_output_file(request, ext)`,
  `ts.diff_results_expected(request, ext)`.  Output and expected file names are derived
  from the test id, so renaming a test renames its expected file.
- `tests/progtests/<tool>/Makefile` - black-box tests of `bin/` programs: run the program
  into `output/`, `diff -u` against `expected/`.  Add a new directory to `subdirs` (or
  `slow_subdirs`) in `tests/progtests/Makefile`.

## Architecture

Packages under `lib/pycbio`, by role:

- `sys` - foundation, imported everywhere.  `fileOps` (compression-transparent `opengz`,
  atomic file creation, `pr*` output functions, tmp files), `cli` (`parseOptsArgsWithLogging`
  splits parsed args into an opts object and a positional-args object; `ErrorHandler`),
  `loggingOps`, `objDict`, `symEnum` (`SymEnum` enum whose members parse from and format to
  their names), `typeOps`, `testingSupport`, `testCaseBase`.
- `tsv` - `TsvReader` yields `TsvRow` objects with attribute access per column, optional
  `typeMap` coercion and `rowClass` subclassing; `TsvWriter`, `TabFile`/`TabFileReader` for
  headerless data.  This is the tabular layer; pandas is not used.
- `hgdata` - browser and genomics file formats.  Each format module follows the same shape:
  a record class (`Bed`, `Psl`, `GenePred`, `Coords`), a `*Reader` generator over a file,
  sometimes a `*Table` for whole-file in-memory access, and a matching `*Sqlite` module whose
  tables subclass `hgSqlite.HgSqliteTable` for random access from cluster jobs.  `rangeFinder`
  and `binnerSA` provide the browser binning and range-overlap queries; `coords.Coords` is an
  immutable namedtuple used as the common interval type.
- `db` - `sqliteOps`, `mysqlOps` connection and cursor context managers under the `*Sqlite`
  and `*MySqlReader` classes.
- `snakemake` - `batch.py` fans one workflow stage out over a cluster as a single snakemake
  rule; the contract with a batch system (job file of shell command lines, blocking launcher,
  non-zero exit on any failure, cwd at workflow root) is documented at the top of that file.
  `ParasolBatch` and `SlurmBatch` implement it.  Also `productScan` and `timing`.
- `ncbi`, `gencode`, `align`, `stats`, `hgbrowser`, `html`, `distrib` - format parsers and
  generators for their respective sources; `distrib/parasol.py` wraps the UCSC `para` command.

Error handling: `pycbio.PycbioException` is the base.  Adding `NoStackError` as a base marks
an exception as a user-input error, which makes `cli.ErrorHandler` print the message without a
stack trace; `PycbioDataError` is the ready-made one for bad input data.  Raise a chained
exception to add file and line context rather than warning and continuing.

`bin/` scripts are standalone: each inserts `../lib` at the front of `sys.path` so it runs
from a checkout without installation, then imports `pycbio`.  New scripts must be added to
the `scripts` list in `setup.py`.

## Conventions

- PEP-8, except the flake8 ignores in `setup.cfg`; end Python source files with a newline.
- Library functions, methods, and attributes are camelCase (`ensureFileDir`, `numStdCols`).
  `sys/testingSupport.py` is deliberately snake_case to match pytest.
- Would like to move to snakeCase for new code.
- Underscore naming rules are in `doc/conventions.txt`: `_leading` is module internal,
  `__leading` is class private.
- Record classes that are hot in loops use `__slots__`; keep that when subclassing.
- `doc/issues.org` and `doc/ideas.org` hold the running defect and design notes; in-code
  FIXMEs cross-reference them.
