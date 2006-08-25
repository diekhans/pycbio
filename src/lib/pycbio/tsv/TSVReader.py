"""TSV reading classes"""
import sys
from pycbio.sys import fileOps
from pycbio.tsv.TSVRow import TSVRow
from pycbio.tsv.TSVError import TSVError

# FIXME:  pass owndership of row to Row instead of having Row inherit from list
# FIXME: create error with file name/line number
# FIMXE: carefully consider naming of functions in Row, as they could
#  conflict with fields.  Maybe put in a base-class??
# FIXME: put in same module as TSV
# FIXME: TSVError and preserving the traceback is a pain
# FIXME: is colMap needed any more???
# FIXME: need to add write stuff. (see GeneCheck), where str() is called on
#        alfor all column ty

class TSVReader(object):
    """Class for reading TSV files.  Reads header and builds column name to
    column index map.  After a next, object contains a row and each column
    becomes a field name.  It is also indexable by column name or int index.
    Columns can be automatically type converted by column name."""

    def _readHeader(self):
        line = self.inFh.readline()
        line = line[0:-1]  # do first to catch blank line
        if (line == ""):
            raise TSVError("empty TSV file or header", reader=self),sys.exc_info()[2]
        if line[0] == '#':
            line = line[1:]
        if self.isRdb:
            self.inFh.readline() # skip format line
        columns = line.split("\t")
        self._setupColumns(columns)

    def _setupColumns(self, columns):
        # n.b. columns could be passed in from client, must copy
        self.columns = []
        self.colMap = {}
        i = 0
        for col in columns:
            col = intern(col)
            self.columns.append(col)
            self.colMap[col] = i
            i += 1

    def _initColTypes(self, typeMap, defaultColType):
        "save col types as column indexed list"
        if typeMap != None:
            # build from type map
            self.colTypes = []
            for col in self.columns:
                self.colTypes.append(typeMap.get(col, defaultColType))
        elif defaultColType != None:
            # fill in colTypes from default
            self.colTypes = []
            for i in xrange(len(self.columns)):
                self.colTypes.append(defaultColType)

    def __init__(self, fileName, rowClass=None, typeMap=None, defaultColType=None, isRdb=False,
                 columns=None, ignoreExtraCols=False):
        """Open TSV file and read header intp object.  Removes leading # from
        UCSC header.

        typeMap - if specified, it maps column names to the type objects to
            use to convert the column.  Unspecified columns will not be
            converted. Key is the column name, value can be either a type
            or a tuple of (parseFunc, formatFunc).  If a type is use,
            str() is used to convert to a printable value.
        defaultColType - if specified, type of unspecified columns
        columns - if specified, the column names to use.  The header
            should not be in the file.
        """
        self.fileName = fileName
        self.lineNum = 0
        self.rowClass = rowClass
        if rowClass == None:
            self.rowClass = TSVRow
        self.isRdb = isRdb
        self.colTypes = None
        self.ignoreExtraCols = ignoreExtraCols
        self.inFh = fileOps.opengz(fileName, "r")
        try:
            if columns:
                self._setupColumns(columns)
            else:
                self._readHeader()
            self._initColTypes(typeMap, defaultColType)
        except Exception, e:
            self.inFh.close()
            raise

    def close(self):
        """close file, keeping column map around.  Called automatically
        by iter on EOF."""
        if self.inFh != None:
            self.inFh.close()
        self.inFh = None

    def __iter__(self):
        return self

    def next(self):
        self.lineNum += 1
        line = self.inFh.readline()
        if (line == ""):
            self.close();
            raise StopIteration
        line = line[0:-1]  # drop newline
        row = line.split("\t")
        if ((self.ignoreExtraCols and (len(row) < len(self.columns)))
            or ((not self.ignoreExtraCols) and (len(row) != len(self.columns)))):
            self.close()
            raise TSVError("row has %d columns, expected %d" %
                           (len(row), len(self.columns)),
                           reader=self)
        return self.rowClass(self, row)


