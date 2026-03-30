# Copyright 2006-2025 Mark Diekhans
"""TSV writing classes"""
import csv
from pycbio.sys import fileOps
from pycbio.tsv.tsvRow import TsvRow
from pycbio.tsv.tsvColumns import columnsSpecBuild


class TsvWriter:
    """Class for writing TSV files with column definitions and optional
    type formatting.  Supports writing from dicts, lists, tuples,
    namedtuples, TsvRow objects, or any object with attributes matching
    column names.

    If the input is a list or tuple, values are assumed to be in column order.
    For dicts and objects with attributes, values are looked up by column name.

    Supports writing to compressed files (.gz, .bz2) via opengz.
    Can be used as a context manager.
    """

    def __init__(self, fileName, *, columns, typeMap=None, defaultColType=None,
                 outFh=None, dialect=csv.excel_tab, encoding=None, errors=None):
        """
        :param fileName: Path to the output TSV file, unless `outFh` is provided.
        :param columns: List of column names.
        :param typeMap: Dictionary mapping column names to either a type or a
            (parseFunc, formatFunc) tuple.  Only the formatFunc is used for writing.
        :param defaultColType: Type to use for columns not listed in `typeMap`.
        :param outFh: An open file-like object to write to instead of `fileName`.
            It will not be closed automatically.
        :param dialect: A `csv.Dialect` instance or dialect name.
        :param encoding: Optional text encoding (e.g., 'utf-8').
        :param errors: Optional error handling strategy.
        """
        self.fileName = fileName
        self.columnSpecs = columnsSpecBuild(columns, typeMap, defaultColType)
        self.outFh = None
        self._shouldClose = False
        self._open(fileName, outFh, dialect, encoding, errors)
        self._writeHeader()

    @property
    def columns(self):
        "column names"
        return self.columnSpecs.columns

    def _open(self, fileName, outFh, dialect, encoding, errors):
        if outFh is not None:
            self.outFh = outFh
            self._shouldClose = False
        else:
            self.outFh = fileOps.opengz(fileName, "w", encoding=encoding, errors=errors)
            self._shouldClose = True
        self._writer = csv.writer(self.outFh, dialect=dialect, lineterminator='\n')

    def close(self):
        """Close the file if this object opened it."""
        if self._shouldClose and self.outFh is not None:
            self.outFh.close()
            self.outFh = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def _writeHeader(self):
        """Write the column header line."""
        self._writer.writerow(self.columns)

    def _rowFromSequence(self, row):
        """Format a list/tuple, assuming values are in column order."""
        return [self.columnSpecs.fmtValue(i, row[i]) for i in range(len(self.columns))]

    def _rowFromMapping(self, row):
        """Format a dict-like object, looking up values by column name."""
        return [self.columnSpecs.fmtValue(i, row[col]) for i, col in enumerate(self.columns)]

    def _rowFromObject(self, row):
        """Format an object with attributes matching column names."""
        return [self.columnSpecs.fmtValue(i, getattr(row, col)) for i, col in enumerate(self.columns)]

    def _formatRow(self, row):
        """Convert a row to a list of formatted strings."""
        if isinstance(row, dict):
            return self._rowFromMapping(row)
        elif isinstance(row, TsvRow):
            return self._rowFromObject(row)
        elif isinstance(row, tuple) and hasattr(row, '_fields'):
            # namedtuple — use attribute names, not positions
            return self._rowFromObject(row)
        elif isinstance(row, (list, tuple)):
            return self._rowFromSequence(row)
        else:
            # object with attributes
            return self._rowFromObject(row)

    def writeRow(self, row):
        """Write a single row.  Row can be a list, tuple, dict, TsvRow,
        or any object with attributes matching column names."""
        self._writer.writerow(self._formatRow(row))

    def writeColumns(self, **kwargs):
        """Write a row using keyword arguments for column values.
        Missing columns get empty string."""
        self._writer.writerow([self.columnSpecs.fmtValue(i, kwargs.get(col))
                               for i, col in enumerate(self.columns)])

    def writeRows(self, rows):
        """Write multiple rows."""
        for row in rows:
            self.writeRow(row)
