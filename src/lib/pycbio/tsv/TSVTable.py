from pycbio.tsv.TSVReader import TSVReader
from pycbio.tsv.TSVError import TSVError
from pycbio.sys.MultiDict import MultiDict
import sys

# FIX: maybe make each index it's own class to handle uniq check, etc.

class TSVTable(list):
    """Class for reading and writing TSV files. Stores rows as a list of Row
    objects. Columns are indexed by name.

    indices - attribute has a dict or MultiDict per keyed columns.
    """
    class Indices (object):
        """attrs are dynamically added to per-class index"""

        def __getitem__(self, key):
            return self.__dict__[key]

    def _createIndex(self, keyCol, dictClass):
        "create an index for a column"
        if not self.colMap.has_key(keyCol):
            raise TSVError("key column \"" + keyCol + "\" is not defined")
        self.indices.__dict__[keyCol] = dictClass()

    def _createIndices(self, keyCols, dictClass):
        "keyCols maybe string or seq of strings"
        if type(keyCols) == str:
            self._createIndex(keyCols, dictClass)
        else:
            for kc in keyCols:
                self._createIndex(kc, dictClass)

    def _buildIndices(self, idCol, uniqKeyCols, multiKeyCols):
        self.indices = TSVTable.Indices()
        self.idCol = idCol
        if idCol != None:
            self._createIndex(idCol, dict)
            self.idColDict = self.indices[idCol]
        if uniqKeyCols != None:
            self._createIndices(uniqKeyCols, dict)
        if multiKeyCols != None:
            self._createIndices(multiKeyCols, MultiDict)

    def _buildColDictTbl(self):
        """build an array, index by column number, of dict objects, or None if not
        indexed.  Used when loading rows. """
        if len(self.indices.__dict__) == 0:
            return None
        tbl = []
        for iCol in xrange(len(self.columns)):
            tbl.append(self.indices.__dict__.get(self.columns[iCol]))
        return tbl

    def _indexCol(self, iCol, colDict, col, row):
        if (type(colDict) == dict) and colDict.get(col):
            raise Exception("column " + self.columns[iCol]+ " unique index value already entered: " + str(col) + " from " + str(row))
        else:
            colDict[col] = row
            
    def _indexRow(self, colDictTbl, row):
        for i in xrange(len(row)):
            if colDictTbl[i] != None:
                self._indexCol(i, colDictTbl[i], row[i], row)
        
    def _readBody(self, reader):
        colDictTbl = self._buildColDictTbl()
        for row in reader:
            self.append(row)
            if colDictTbl != None:
                self._indexRow(colDictTbl, row)


    def __init__(self, fileName, idCol=None, uniqKeyCols=None, multiKeyCols=None,
                 rowClass=None, typeMap=None, defaultColType=None, isRdb=False,
                 columns=None, ignoreExtraCols=False):
        """Read TSV file into the object
        
        idCol - if specified,  the name of a column to use for getById(), which must have
            unique values. (obsolete)
        uniqKeyCols - name or names of columns to index with uniq keys,
            can be string or sequence
        multiKeyCols - name or names of columns to index, allowing multiple keys.
            can be string or sequence
        typeMap - if specified, it maps column names to the type objects to
            use to convert the column.  Unspecified columns will not be
            converted. Key is the column name, value can be either a type
            or a tuple of (parseFunc, formatFunc).  If a type is use,
            str() is used to convert to a printable value.
        defaultColType - if specified, type of unspecified columns
        isRdb - true if this is an RDB file.
        """
        reader = TSVReader(fileName, rowClass=rowClass, typeMap=typeMap, defaultColType=defaultColType, isRdb=isRdb, columns=columns, ignoreExtraCols=ignoreExtraCols)
        try:
            self.columns = reader.columns
            self.colTypes = reader.colTypes
            self.colMap = reader.colMap
            self._buildIndices(idCol, uniqKeyCols, multiKeyCols)
            self._readBody(reader)
        except Exception, e:
            raise
        #FIXME: raise TSVError("load failed", reader=reader, cause=e),sys.exc_traceback

    def getById(self, id):
        "get a row by the id column"
        return self.idColDict[id]

    def addColumn(self, colName, initValue=None, colType=None):
        "add a column to all rows in the table"
        if self.colMap.has_key(colName):
            raise TSVError("column \"" + colName + "\" is already defined")
        self.colMap[colName] = len(self.columns)
        if colType:
            assert(self.colTypes)
            self.colTypes.append(colType)
        elif self.colTypes:
            self.colTypes.append(None)
        self.columns.append(colName)

        # add column to each row
        for row in self:
            row.__dict__[colName] = initValue

    def write(self, fh):
        fh.write(str.join("\t", self.columns))
        fh.write("\n")
        for row in self:
            row.write(fh)

# FIXME: duped in TabFile, also file ops
def tsvPrRow(fh, row):
    """Print a row (list or tupe) to a tab file.
    does string conversions on columns"""
    cnt = 0;
    for col in row:
        if cnt > 0:
            fh.write("\t")
        fh.write(str(col))
        cnt += 1
    fh.write("\n")
