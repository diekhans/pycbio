# Copyright 2006-2018 Mark Diekhans
"""
Storage of PSL format tables in sqlite for use in cluster jobs and other
random access uses.
"""
from pycbio.hgdata.hgSqlite import HgSqliteTable
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.rangeFinder import Binner
from pycbio.tsv import TabFileReader


class PslSqliteTable(HgSqliteTable):
    """
    Storage for PSL alignments.  Psl objects, or raw sql rows can be
    return.  Raw return is to save object creation overhead when results are
    going to be written to a file.
    """
    createSql = """CREATE TABLE {table} (
            bin INT UNSIGNED NOT NULL,
            matches INT UNSIGNED NOT NULL,
            misMatches INT UNSIGNED NOT NULL,
            repMatches INT UNSIGNED NOT NULL,
            nCount INT UNSIGNED NOT NULL,
            qNumInsert INT UNSIGNED NOT NULL,
            qBaseInsert INT UNSIGNED NOT NULL,
            tNumInsert INT UNSIGNED NOT NULL,
            tBaseInsert INT UNSIGNED NOT NULL,
            strand TEXT NOT NULL,
            qName TEXT NOT NULL,
            qSize INT UNSIGNED NOT NULL,
            qStart INT UNSIGNED NOT NULL,
            qEnd INT UNSIGNED NOT NULL,
            tName TEXT NOT NULL,
            tSize INT UNSIGNED NOT NULL,
            tStart INT UNSIGNED NOT NULL,
            tEnd INT UNSIGNED NOT NULL,
            blockCount INT UNSIGNED NOT NULL,
            blockSizes TEXT NOT NULL,
            qStarts TEXT NOT NULL,
            tStarts TEXT NOT NULL)"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_tName_bin ON {table} (tName, bin)""",
        """CREATE INDEX {table}_qname ON {table} (qName)"""]

    # doesn't include bin
    columnNames = ("matches", "misMatches", "repMatches", "nCount",
                   "qNumInsert", "qBaseInsert", "tNumInsert", "tBaseInsert",
                   "strand", "qName", "qSize", "qStart", "qEnd", "tName",
                   "tSize", "tStart", "tEnd", "blockCount", "blockSizes",
                   "qStarts", "tStarts")
    columnNamesBin = ("bin",) + columnNames

    def __init__(self, conn, table, create=False):
        super(PslSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loadsWithBin(self, binnedRows):
        """load PSLs rows which already have bin column"""
        self._inserts(self.insertSql, self.columnNamesBin, binnedRows)

    def loads(self, rows):
        """load rows, which can be list-like or Psl objects, adding bin"""
        binnedRows = []
        for row in rows:
            if isinstance(row, Psl):
                row = row.toRow()
            bin = Binner.calcBin(int(row[15]), int(row[16]))
            binnedRows.append((bin,) + tuple(row))
        self.loadsWithBin(binnedRows)

    # FIXME: dups code above
    @staticmethod
    def _binPslRow(row):
        "add bin; note modifies row"
        row.insert(0, Binner.calcBin(int(row[15]), int(row[16])))
        return row

    def loadPslFile(self, pslFile):
        """load a PSL file or file-like object, adding bin"""
        rows = []
        for row in TabFileReader(pslFile):
            rows.append(self._binPslRow(row))
        self.loadsWithBin(rows)

    @staticmethod
    def _getRowFactory(raw):
        return None if raw else lambda cur, row: Psl.fromRow(row)

    def getAll(self, raw=False):
        """Generator for PSLs for all rows in a table. If raw is
        specified, don't convert to Psl objects if raw is True"""
        sql = "SELECT {columns} FROM {table}"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw))

    def getByQName(self, qName, raw=False):
        """get list of Psl objects (or raw rows) for all alignments for qName """
        sql = "SELECT {columns} FROM {table} WHERE qName = ?"
        return list(self.queryRows(sql, self.columnNames, self._getRowFactory(raw), qName))

    def getByOid(self, startOid, endOid, raw=False):
        """Generator for PSLs for a range of OIDs (1/2 open).  If raw is
        specified, don't convert to Psl objects if raw is True"""
        sql = "SELECT {columns} FROM {table} WHERE (oid >= ?) AND (oid < ?)"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw), startOid, endOid)

    def getTRangeOverlap(self, tName, tStart, tEnd, strand=None, extraWhere=None, raw=False):
        """Get alignments overlapping target range. To query the whole
        sequence, set tStart and tEnd to None.  Don't convert to Psl objects
        if raw is True.  Strand should match the strand value in the table
        (one or two) and maybe a list of multiple value.  The where is ANDed
        with the query if supplied."""
        if tStart is None:
            rangeWhere = "(tName = '{}')".format(tName)
        else:
            rangeWhere = Binner.getOverlappingSqlExpr("bin", "tName", "tStart", "tEnd", tName, tStart, tEnd)
        sql = "SELECT {{columns}} FROM {{table}} WHERE {}".format(rangeWhere)
        if strand is not None:
            if isinstance(strand, str):
                strand = [strand]
            sql += " AND (strand in ({}))".format(','.join(["'{}'".format(s) for s in strand]))
        if extraWhere is not None:
            sql += " AND ({})".format(extraWhere)
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw))
