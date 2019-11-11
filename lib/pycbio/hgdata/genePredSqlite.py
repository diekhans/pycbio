# Copyright 2006-2018 Mark Diekhans
"""
Storage of genePred data from sqlite for use in cluster jobs and other
random access uses.
"""
from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()
from pycbio.db import sqliteOps
from pycbio.hgdata.hgSqlite import HgSqliteTable
from pycbio.hgdata.genePred import GenePred
from pycbio.hgdata.rangeFinder import Binner
from pycbio.tsv import TabFileReader


class GenePredSqliteTable(HgSqliteTable):
    """
    Storage for genePred annotations.  GenePred  objects, or raw sql rows can beg38
    return.  Raw return is to save object creation overhead when results are
    going to be written to a file.
    """
    createSql = """CREATE TABLE {table} (
            bin INT UNSIGNED NOT NULL,
            name TEXT NOT NULL,
            chrom TEXT NOT NULL,
            strand CHAR NOT NULL,
            txStart INT UNSIGNED NOT NULL,
            txEnd INT UNSIGNED NOT NULL,
            cdsStart INT UNSIGNED NOT NULL,
            cdsEnd INT UNSIGNED NOT NULL,
            exonCount INT UNSIGNED NOT NULL,
            exonStarts TEXT NOT NULL,
            exonEnds TEXT NOT NULL,
            score INT DEFAULT NULL,
            name2 TEXT NOT NULL,
            cdsStartStat TEXT NOT NULL,
            cdsEndStat TEXT NOT NULL,
            exonFrames TEXT NOT NULL)"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_chrom_bin ON {table} (chrom, bin)""",
        """CREATE INDEX {table}_name ON {table} (name)"""]

    # doesn't include bin
    columnNames = ("name", "chrom", "strand", "txStart", "txEnd", "cdsStart",
                   "cdsEnd", "exonCount", "exonStarts", "exonEnds", "score",
                   "name2", "cdsStartStat", "cdsEndStat", "exonFrames")
    columnNamesBin = ("bin",) + columnNames

    def __init__(self, conn, table, create=False):
        super(GenePredSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loadsWithBin(self, binnedRows):
        """load genePred rows which already have bin column"""
        self._inserts(self.insertSql, self.columnNamesBin, binnedRows)

    def loads(self, rows):
        """load rows, which can be list-like or genePred objects, adding bin"""
        binnedRows = []
        for row in rows:
            if isinstance(row, GenePred):
                row = row.getRow()
            bin = Binner.calcBin(int(row[3]), int(row[4]))
            binnedRows.append((bin,) + tuple(row))
        self.loadsWithBin(binnedRows)

    def loadGenePredFile(self, genePredFile):
        """load a genePred file, adding bin"""
        rows = [row for row in TabFileReader(genePredFile)]
        self.loads(rows)

    @staticmethod
    def _getRowFactory(raw):
        return None if raw else lambda cur, row: GenePred(row)

    def getAll(self, raw=False):
        """Generator for all genePreds in a table. Don't convert to GenePred
        objects if raw is True."""
        sql = "SELECT {columns} FROM {table}"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw))

    def getNames(self):
        sql = "SELECT distinct name FROM {table}"
        with sqliteOps.SqliteCursor(self.conn, rowFactory=self._getRowFactory(raw=True)) as cur:
            cur.execute(sql)
            return [row[0] for row in cur]

    def getByName(self, name, raw=False):
        """generator for list of GenePred objects (or raw rows) for all alignments for name """
        sql = "SELECT {columns} FROM {table} WHERE name = ?"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw), name)

    def getByOid(self, startOid, endOid, raw=False):
        """Generator for genePreds for a range of OIDs (1/2 open).  If raw is
        specified, don't convert to GenePred objects if raw is True."""
        sql = "SELECT {columns} FROM {table} WHERE (oid >= ?) and (oid < ?)"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw), startOid, endOid)

    def getRangeOverlap(self, chrom, start, end, strand=None, raw=False):
        """Get annotations overlapping range To query the whole sequence, set
        start and end to None.  If raw is specified. Don't convert to GenePred
        objects if raw is True."""
        if start is None:
            rangeWhere = "(chrom = '{}')".format(chrom)
        else:
            rangeWhere = Binner.getOverlappingSqlExpr("bin", "chrom", "txStart", "txEnd", chrom, start, end)
        sql = "SELECT {{columns}} FROM {{table}} WHERE {}".format(rangeWhere)
        sqlArgs = []
        if strand is not None:
            sql += " AND (strand = ?)"
            sqlArgs.append(strand)
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw), *sqlArgs)
