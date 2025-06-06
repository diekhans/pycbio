# Copyright 2006-2025 Mark Diekhans
"""TSV reading classes"""
import sys
import csv
from pycbio.sys import fileOps
from pycbio.tsv.tsvRow import TsvRow
from pycbio.tsv import TsvError

csv.field_size_limit(sys.maxsize)


# typeMap converter for str types were empty represents None
strOrNoneType = (lambda v: None if (v == "") else v,
                 lambda v: "" if (v is None) else v)

# typeMap converter for int types were empty represents None
intOrNoneType = (lambda v: None if (v == "") else int(v),
                 lambda v: "" if (v is None) else str(v))

floatOrNoneType = (lambda v: None if (v == "") else float(v),
                   lambda v: "" if (v is None) else str(v))


class printf_basic_dialect(csv.Dialect):
    """Describes the usual properties for TSV files generated by printf, etc.  Common
    in bioinformatics.  Quotes can be included in data, etc.
    """
    delimiter = '\t'
    quotechar = None
    doublequote = False
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_NONE

def _dehashHeader(row):
    if (len(row) > 0) and row[0].startswith('#'):
        # sometimes there is a space after #
        row[0] = row[0][1:].strip()

class TsvReader:
    """Class for reading TSV files.  Reads header and builds column name to
    column index map.  After a next, object contains a row and each column
    becomes a field name.  It is also can be indexed by column name or int
    index.  Columns can be automatically type converted by column name.  This
    can also read from a dbapi cursor object (must set allowEmpty to true)

    If the first character of the header is '#', the '#' and following spaces
    are ignored and not part of the first column name.
    """

    def __init__(self, fileName, *, rowClass=None, typeMap=None, defaultColType=None, columns=None, columnNameMapper=None,
                 ignoreExtraCols=False, inFh=None, allowEmpty=False, dialect=csv.excel_tab,
                 encoding=None, errors=None):
        """Open TSV file and read header into object.  Removes leading # from
        UCSC header.

        fileName - name of file, opened unless inFh is specified
        rowClass - class or factory function to use for a row. Must take
            TsvReader and a list of columns values.
        typeMap - if specified, it maps column names to the type objects to
            use to convert the column.  Unspecified columns will not be
            converted. Key is the column name, value can be either a type
            or a tuple of (parseFunc, formatFunc).  If a type is use,
            str() is used to convert to a printable value.
        defaultColType - if specified, type of unspecified columns
        columns - if specified, the column names to use.  The header
            should not be in the file.
        columnNameMapper - function to map column names to the internal name.
        ignoreExtraCols - should extra columns be ignored?
        inFh - If not None, this is used as the open file, rather than
          opening it.  Will not be closed.
        allowEmpty - an empty input results in an EOF rather than an error.
        dialect - a csv dialect object or name.
        """
        self.fileName = fileName
        self.columns = []
        # external column name, before mapping with columnNameMapper
        if columnNameMapper is None:
            self.extColumns = self.columns
        else:
            self.extColumns = []
        self.colMap = {}
        self.fileName = fileName
        self.rowClass = rowClass
        if rowClass is None:
            self.rowClass = TsvRow
        self.colTypes = None
        self.ignoreExtraCols = ignoreExtraCols
        self.inFh = None
        self._shouldClose = False
        self._reader = None

        try:
            self._openTsv(fileName, typeMap, defaultColType, columns, columnNameMapper, inFh,
                          allowEmpty, dialect, encoding, errors)
        except Exception as ex:
            self._closeTsv()
            raise TsvError(f"open of TSV failed {fileName}") from ex

    def _openTsv(self, fileName, typeMap, defaultColType, columns, columnNameMapper, inFh,
                 allowEmpty, dialect, encoding, errors):
        if inFh is not None:
            self.inFh = inFh
            self._shouldClose = False
        else:
            self.inFh = fileOps.opengz(fileName, encoding=encoding, errors=errors)
            self._shouldClose = True
        self._reader = csv.reader(self.inFh, dialect=dialect)
        if columns is None:
            columns = self._readHeader(allowEmpty)
        self._setupColumns(columns, columnNameMapper)
        self._initColTypes(typeMap, defaultColType)

    def _closeTsv(self):
        "close if we opened the file"
        if self._shouldClose:
            self.close()

    def close(self):
        """force close of the file if open, even if this object didn't open
        it.  Normally, close is handled when end of file is reached"""
        if self.inFh is not None:
            self.inFh.close()
            self.inFh = None

    @property
    def lineNum(self):
        return self._reader.line_num

    def _readHeader(self, allowEmpty):
        try:
            row = next(self._reader)
            _dehashHeader(row)
            return row
        except StopIteration:
            if not allowEmpty:
                raise TsvError("empty TSV file", reader=self)
            return []

    def _setupColumns(self, columns, columnNameMapper):
        # n.b. columns could be passed in from client, must copy
        i = 0
        for col in columns:
            if columnNameMapper is not None:
                self.extColumns.append(col)
                col = columnNameMapper(col)
            self.columns.append(col)
            if col in self.colMap:
                raise TsvError("Duplicate column name: '{}'".format(col))
            self.colMap[col] = i
            i += 1

    def _setColumnTypes(self, typeMap, defaultColType):
        "build from type map"
        self.colTypes = []
        for col in self.columns:
            self.colTypes.append(typeMap.get(col, defaultColType))

    def _setDefaultColumnTypes(self, defaultColType):
        "default all colums"
        self.colTypes = []
        for i in range(len(self.columns)):
            self.colTypes.append(defaultColType)

    def _initColTypes(self, typeMap, defaultColType):
        "save col types as column indexed list"
        if typeMap is not None:
            self._setColumnTypes(typeMap, defaultColType)
        elif defaultColType is not None:
            self._setDefaultColumnTypes(defaultColType)

    def _parseColumnWithTypeMap(self, row, iCol):
        ct = self.colTypes[iCol]
        cv = ct[0] if isinstance(ct, tuple) else ct
        try:
            # can be None to have formatter but not parser
            if cv is not None:
                row[iCol] = cv(row[iCol])
        except Exception as ex:
            raise TsvError("Error converting TSV column {} ({}) to object, value \"{}\"".format(iCol, self.columns[iCol], row[iCol])) from ex

    def _parseColumns(self, row):
        "converts columns in row in-place, if needed"
        for iCol in range(len(self.columns)):
            self._parseColumnWithTypeMap(row, iCol)

    def _constructRow(self, row):
        if ((self.ignoreExtraCols and (len(row) < len(self.columns))) or ((not self.ignoreExtraCols) and (len(row) != len(self.columns)))):
            raise TsvError("row has {} columns, expected {}".format(len(row), len(self.columns)), reader=self)
        try:
            if self.colTypes is not None:
                self._parseColumns(row)
            return self.rowClass(self, row)
        except Exception as ex:
            raise TsvError("Error converting TSV row to object", self) from ex

    def __iter__(self):
        try:
            for row in self._reader:
                yield self._constructRow(row)
        except Exception as ex:
            raise TsvError("Error reading TSV row", self) from ex
        finally:
            self._closeTsv()

    def _fmtColWithTypes(self, row, iCol):
        col = row[iCol]
        if col is None:
            return ""
        ct = self.colTypes[iCol]
        if type(ct) is tuple:
            return ct[1](col)
        else:
            return str(col)

    def _fmtRowWithTypes(self, row):
        outrow = []
        for iCol in range(len(self.columns)):
            outrow.append(self._fmtColWithTypes(row, iCol))
        return outrow

    def _fmtRowNoTypes(self, row):
        outrow = []
        for iCol in range(len(self.columns)):
            col = row[iCol]
            outrow.append(str(col) if col is not None else '')
        return outrow

    def formatRow(self, row):
        "format row to a list of strings given specified types"
        if self.colTypes is not None:
            return self._fmtRowWithTypes(row)
        else:
            return self._fmtRowNoTypes(row)
