# Copyright 2006-2018 Mark Diekhans
"""
Storage of GENCODE data from UCSC import in sqlite for use in cluster jobs and
other random access uses.
"""
from __future__ import print_function
import sys
from future.standard_library import install_aliases
install_aliases()
from collections import namedtuple
from pycbio.db import sqliteOps
from pycbio.sys import PycbioException
from pycbio.hgdata.hgSqlite import HgSqliteTable, noneIfEmpty
from pycbio.hgdata.rangeFinder import Binner
from pycbio.tsv import TsvReader

# FIXME: binning code redundant with other objects.
# FIXME: needs tests

class GencodeAttrs(namedtuple("GencodeAttrs",
                              ("geneId", "geneName", "geneType", "geneStatus", "transcriptId",
                               "transcriptName", "transcriptType", "transcriptStatus", "havanaGeneId",
                               "havanaTranscriptId", "ccdsId", "level", "transcriptClass", "proteinId"))):
    """Attributes of a GENCODE transcript. New attribute added to table become optional"""
    __slots__ = ()

    def __new__(cls, geneId, geneName, geneType, geneStatus, transcriptId,
                transcriptName, transcriptType, transcriptStatus, havanaGeneId,
                havanaTranscriptId, ccdsId, level, transcriptClass, proteinId=None):
        return super(GencodeAttrs, cls).__new__(cls, geneId, geneName, geneType,
                                                geneStatus, transcriptId,
                                                transcriptName, transcriptType,
                                                transcriptStatus, havanaGeneId,
                                                havanaTranscriptId, ccdsId, level,
                                                transcriptClass, proteinId)


class GencodeAttrsSqliteTable(HgSqliteTable):
    """
    GENCODE attributes table from UCSC databases.
    """
    createSql = """CREATE TABLE {table} (
            geneId TEXT NOT NULL,
            geneName TEXT NOT NULL,
            geneType TEXT NOT NULL,
            geneStatus TEXT DEFAULT NULL,
            transcriptId TEXT NOT NULL,
            transcriptName TEXT NOT NULL,
            transcriptType TEXT NOT NULL,
            transcriptStatus TEXT DEFAULT NULL,
            havanaGeneId TEXT DEFAULT NULL,
            havanaTranscriptId TEXT DEFAULT NULL,
            ccdsId TEXT DEFAULT NULL,
            level INT NOT NULL,
            transcriptClass TEXT NOT NULL,
            proteinId TEXT DEFAULT NULL)"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_geneId ON {table} (geneId)""",
        """CREATE INDEX {table}_geneName ON {table} (geneName)""",
        """CREATE INDEX {table}_geneType ON {table} (geneType)""",
        """CREATE INDEX {table}_transcriptId ON {table} (transcriptId)""",
        """CREATE INDEX {table}_transcriptType ON {table} (transcriptType)""",
        """CREATE INDEX {table}_havanaGeneId ON {table} (havanaGeneId)""",
        """CREATE INDEX {table}_havanaTranscriptId ON {table} (havanaTranscriptId)""",
        """CREATE INDEX {table}_ccdsId ON {table} (ccdsId)""",
        """CREATE INDEX {table}_proteinId ON {table} (proteinId)""",
    ]

    columnNames = GencodeAttrs._fields

    def __init__(self, conn, table, create=False):
        super(GencodeAttrsSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loads(self, rows):
        """load rows, which can be list-like or GencodeAttrs object"""
        self._inserts(self.insertSql, self.columnNames, rows)

    def _loadTsvRow(self, tsvRow):
        "convert to list in column order"
        # None allows for newly added columns at end
        return [getattr(tsvRow, cn, None) for cn in self.columnNames]

    def loadTsv(self, attrsFile):
        """load a GENCODE attributes file, adding bin"""
        typeMap = {"geneStatus": noneIfEmpty,
                   "transcriptStatus": noneIfEmpty,
                   "havanaGeneId": noneIfEmpty,
                   "havanaTranscriptId": noneIfEmpty,
                   "ccdsId": noneIfEmpty,
                   "proteinId": noneIfEmpty,
                   "level": int}
        rows = [self._loadTsvRow(row) for row in TsvReader(attrsFile, typeMap=typeMap)]
        self.loads(rows)

    def _queryRows(self, sql, *queryargs):
        return self.queryRows(sql, self.columnNames, lambda cur, row: GencodeAttrs(*row), *queryargs)

    def getByTranscriptId(self, transcriptId):
        """get the GencodeAttrs object for transcriptId, or None if not found."""
        sql = "SELECT {columns} FROM {table} WHERE transcriptId = ?"
        return next(self._queryRows(sql, transcriptId), None)

    def getrByTranscriptId(self, transcriptId):
        """get the required GencodeAttrs object for transcriptId, or error if not found."""
        attrs = self.getByTranscriptId(transcriptId)
        if attrs is None:
            PycbioException("transcriptId {} not found in {}".format(transcriptId, self.table))
        return attrs

    def getByGeneId(self, geneId):
        """get GencodeAttrs objects for geneId or empty list if not found"""
        sql = "SELECT {columns} FROM {table} WHERE geneId = ?"
        return list(self._queryRows(sql, geneId))

    def getrByGeneId(self, geneId):
        """get required GencodeAttrs objects for geneId or error if not found"""
        attrses = self.getByGeneId(geneId)
        if len(attrses) == 0:
            PycbioException("geneId {} not found in {}".format(geneId, self.table))
        return attrses

    def getGeneIds(self):
        sql = "SELECT DISTINCT geneId FROM {table}"
        return list(self.queryRows(sql, (), lambda cur, row: row[0]))

    def getGeneTranscriptIds(self, geneId):
        sql = "SELECT transcriptId FROM {table} WHERE geneId = ?"
        return list(self.queryRows(sql, (), lambda cur, row: row[0], geneId))


class GencodeTranscriptSource(namedtuple("GencodeTranscriptSource",
                                         ("transcriptId", "source",))):
    """GENCODE transcript source"""
    __slots__ = ()
    pass


class GencodeTranscriptSourceSqliteTable(HgSqliteTable):
    """
    GENCODE transcript source from UCSC databases.
    """
    createSql = """CREATE TABLE {table} (
            transcriptId TEXT NOT NULL,
            source TEXT NOT NULL)"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_transcriptId ON {table} (transcriptId)""",
        """CREATE INDEX {table}_source ON {table} (source)""",
    ]

    columnNames = GencodeTranscriptSource._fields

    def __init__(self, conn, table, create=False):
        super(GencodeTranscriptSourceSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loads(self, rows):
        """load rows, which can be list-like or GencodeTranscriptSource object"""
        self._inserts(self.insertSql, self.columnNames, rows)

    def _loadTsvRow(self, tsvRow):
        "convert to list in column order"
        return [getattr(tsvRow, cn) for cn in self.columnNames]

    def loadTsv(self, sourceFile):
        """load a GENCODE attributes file, adding bin"""
        rows = [self._loadTsvRow(row) for row in TsvReader(sourceFile)]
        self.loads(rows)

    def _queryRows(self, sql, *queryargs):
        return self.queryRows(sql, self.columnNames, lambda cur, row: GencodeTranscriptSource(row[0], sys.intern(str(row[1]))), *queryargs)

    def getAll(self):
        sql = "select {columns} from {table}"
        return self._queryRows(sql)

    def getByTranscriptId(self, transcriptId):
        """get the GencodeTranscriptSource object for transcriptId, or None if not found."""
        sql = "select {columns} from {table} where transcriptId = ?"
        return next(self._queryRows(sql, transcriptId), None)


class GencodeTranscriptionSupportLevel(namedtuple("GencodeTranscriptionSupportLevel",
                                                  ("transcriptId", "level",))):
    """GENCODE transcription support level"""
    __slots__ = ()
    pass


class GencodeTranscriptionSupportLevelSqliteTable(HgSqliteTable):
    """
    GENCODE transcript support levels from UCSC databases.
    """
    createSql = """CREATE TABLE {table} (
            transcriptId TEXT NOT NULL,
            level INT NOT NULL)"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_transcriptId ON {table} (transcriptId)""",
    ]

    columnNames = GencodeTranscriptionSupportLevel._fields

    def __init__(self, conn, table, create=False):
        super(GencodeTranscriptionSupportLevelSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loads(self, rows):
        """load rows, which can be list-like or GencodeTranscriptionSupportLevel object"""
        self._inserts(self.insertSql, self.columnNames, rows)

    def _loadTsvRow(self, tsvRow):
        "convert to list in column order"
        return [getattr(tsvRow, cn) for cn in self.columnNames]

    def loadTsv(self, sourceFile):
        """load a GENCODE attributes file, adding bin"""
        rows = [self._loadTsvRow(row) for row in TsvReader(sourceFile)]
        self.loads(rows)

    def _queryRows(self, sql, *queryargs):
        return self.queryRows(sql, self.columnNames, lambda cur, row: GencodeTranscriptionSupportLevel(row[0], row[1]), *queryargs)

    def getAll(self):
        sql = "select {columns} from {table}"
        return self._queryRows(sql)

    def getByTranscriptId(self, transcriptId):
        """get the GencodeTranscriptionSupportLevel object for transcriptId, or None if not found."""
        sql = "select {columns} from {table} where transcriptId = ?"
        return next(self._queryRows(sql, transcriptId), None)


class GencodeTag(namedtuple("GencodeTag",
                            ("transcriptId", "tag",))):
    """GENCODE transcription support level"""
    __slots__ = ()
    pass


class GencodeTagSqliteTable(HgSqliteTable):
    """
    GENCODE transcript tags from UCSC databases.
    """
    createSql = """CREATE TABLE {table} (
            transcriptId TEXT NOT NULL,
            tag TEXT NOT NULL)"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_transcriptId ON {table} (transcriptId)""",
        """CREATE INDEX {table}_tag ON {table} (tag)""",
    ]

    columnNames = GencodeTag._fields

    def __init__(self, conn, table, create=False):
        super(GencodeTagSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loads(self, rows):
        """load rows, which can be list-like or GencodeTag object"""
        self._inserts(self.insertSql, self.columnNames, rows)

    def _loadTsvRow(self, tsvRow):
        "convert to list in column order"
        return [getattr(tsvRow, cn) for cn in self.columnNames]

    def loadTsv(self, sourceFile):
        """load a GENCODE attributes file, adding bin"""
        rows = [self._loadTsvRow(row) for row in TsvReader(sourceFile)]
        self.loads(rows)

    def _queryRows(self, sql, *queryargs):
        return self.queryRows(sql, self.columnNames, lambda cur, row: GencodeTag(row[0], row[1]), *queryargs)

    def getAll(self):
        sql = "SELECT {columns} FROM {table}"
        return self._queryRows(sql)

    def getByTranscriptId(self, transcriptId):
        """get the GencodeTag objects for transcriptId, or empty if not found."""
        sql = "SELECT {columns} FROM {table} WHERE transcriptId = ?"
        return self._queryRows(sql, transcriptId)


class GencodeGene(namedtuple("GencodeGene",
                             ("chrom", "chromStart", "chromEnd", "name",
                              "score", "strand", "geneType", "geneName"))):
    """GENCODE gene bounds.  A BED-6 based object with gene bounds and
    type. 'name' is the geneId, score is unused."""
    __slots__ = ()

    def __new__(cls, chrom, chromStart, chromEnd, name, score, strand, geneType, geneName):
        return super(GencodeGene, cls).__new__(cls, chrom, int(chromStart), chromEnd, int(name),
                                               int(score), strand, geneType, geneName)


class GencodeGeneSqliteTable(HgSqliteTable):
    """Table of GencodeGene objects, name might not be unique due to PAR"""
    createSql = """CREATE TABLE {table} (
             bin INT UNSIGNED NOT NULL,
             chrom TEXT NOT NULL,
             chromStart INT UNSIGNED NOT NULL,
             chromEnd INT UNSIGNED NOT NULL,
             name TEXT NOT NULL,
             score INT UNSIGNED NOT NULL DEFAULT 0,
             strand TEXT NOT NULL,
             geneType TEXT NOT NULL,
             geneName TEXT NOT NULL
        """
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = [
        """CREATE INDEX {table}_chrom_bin ON {table} (chrom, bin)""",
        """CREATE INDEX {table}_name ON {table} (name)""",
        """CREATE INDEX {table}_geneType ON {table} (geneId)"""]

    # doesn't include bin
    columnNames = ("chrom", "chromStart", "chromEnd", "name",
                   "score", "strand", "geneType", "geneName")
    columnNamesBin = ("bin",) + columnNames

    def __init__(self, conn, table, create=False):
        super(GencodeGeneSqliteTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loadsWithBin(self, binnedRows):
        """load GencodeGene rows which already have bin column"""
        self._inserts(self.insertSql, self.columnNamesBin, binnedRows)

    def loads(self, rows):
        """load rows, which can be list-like or GencodeGene objects, adding bin"""
        binnedRows = []
        for row in rows:
            bin = Binner.calcBin(int(row[1]), int(row[2]))
            binnedRows.append((bin,) + tuple(row))
        self.loadsWithBin(binnedRows)

    @staticmethod
    def _getRowFactory(raw):
        return None if raw else lambda cur, row: GencodeGene(row)

    def getAll(self, raw=False):
        """Generator for all GencodeGene in a table. Don't convert to GencodeGene
        objects if raw is True."""
        sql = "SELECT {columns} FROM {table}"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw))

    def getNames(self):
        sql = "SELECT distinct name FROM {table}"
        with sqliteOps.SqliteCursor(self.conn, rowFactory=self._getRowFactory(raw=True)) as cur:
            cur.execute(sql)
        return [row[0] for row in cur]

    def getByName(self, name, raw=False):
        """generator for list of GencodeGene objects (or raw rows) for all alignments for name """
        sql = "SELECT {columns} FROM {table} WHERE name = ?"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw), name)

    def getByOid(self, startOid, endOid, raw=False):
        """Generator for GencodeGenes for a range of OIDs (1/2 open).  If raw is
        specified, don't convert to GencodeGene objects if raw is True."""
        sql = "SELECT {columns} FROM {table} WHERE (oid >= ?) and (oid < ?)"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw), startOid, endOid)

    def getRangeOverlap(self, chrom, start, end, strand=None, raw=False):
        """Get annotations overlapping range To query the whole sequence, set
        start and end to None.  If raw is specified. Don't convert to GencodeGene
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
