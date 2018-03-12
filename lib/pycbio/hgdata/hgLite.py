# Copyright 2006-2016 Mark Diekhans
"""
Storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
from __future__ import print_function
import six
from future.standard_library import install_aliases
install_aliases()
from collections import namedtuple
from pycbio.sys import PycbioException
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.genePred import GenePred
from pycbio.tsv import TabFileReader
from pycbio.tsv import TsvReader
from pycbio.hgdata.rangeFinder import Binner
from Bio import SeqIO
import sys
from pycbio.db.sqliteOps import SqliteCursor
# allow sqliteConnect to be imported from this module, as it is so common
from pycbio.db.sqliteOps import sqliteConnect   # noqa: F401

# FIXME: HgLiteTable could become wrapper around a connection,
# and make table operations functions.???  probably not
# FIXME: removed duplicated functions and move to base class or mix-in especially gencode
# FIXME: move generic sqlite to another module.
# FIXME: often hides sql too much (gencode_icedb/general/gencodeDb.py: getGeneIdsStartingInBounds)
# FIXME: maaybe a series of functions to build queryes would be the ticket (binning, in querys, ihserts); this is not that composable.
# FIXME" prefix generators with gen**********
# FIXME: term load is confusing, use read, write, or insert
# FIXME: could this move to peewee, since we can assign primary keys on load;
#        although the table per class is problematic; could dynamically create classes with
#        type(name, bases, dict)
# FIXME: maybe separate table definitions from query construction


def noneIfEmpty(s):
    return s if s != "" else None


class HgLiteTable(object):
    """Base class for SQL list table interface object."""
    def __init__(self, conn, table):
        self.conn = conn
        self.table = table

    def _create(self, createSql):
        self.executes(["DROP TABLE IF EXISTS {table};".format(table=self.table),
                       createSql])

    def _index(self, indexSql):
        if isinstance(indexSql, six.string_types):
            indexSql = [indexSql]
        self.executes(indexSql)

    @staticmethod
    def _joinColNames(columns):
        return ",".join(columns)

    @staticmethod
    def _makeValueTokens(columns):
        "generate `?' for insert values"
        return ",".join(len(columns) * ["?"])

    def _formatSql(self, sql, columns):
        "format {table}, {columns}, and if in sql, {values}"
        return sql.format(table=self.table,
                          columns=self._joinColNames(columns),
                          values=self._makeValueTokens(columns))

    def _insert(self, insertSql, columns, row):
        """insert a row, formatting {table}, {columns}, {values} into sql"""
        with SqliteCursor(self.conn) as cur:
            cur.execute(self._formatSql(insertSql, columns), row)

    def _inserts(self, insertSql, columns, rows):
        """insert multiple rows, formatting {table}, {columns}, {values} into sql"""
        with SqliteCursor(self.conn) as cur:
            cur.executemany(self._formatSql(insertSql, columns), rows)

    def queryRows(self, querySql, columns, rowFactory, *queryargs):
        """run query, formatting {table}, {columns} into sql and generator over results and
        setting row factory"""
        sql = querySql.format(table=self.table, columns=self._joinColNames(columns))
        with SqliteCursor(self.conn, rowFactory=rowFactory) as cur:
            cur.execute(sql, queryargs)
            for row in cur:
                yield row

    def query(self, querySql, columns, *queryargs):
        """run query, formatting {table} into sql and generator over result rows """
        return self.queryRows(querySql, columns, None, *queryargs)

    def execute(self, querySql):
        """execute a query formatting {table} into sql, with no results"""
        with SqliteCursor(self.conn) as cur:
            cur.execute(querySql.format(table=self.table))

    def executes(self, querySqls):
        """execute multiple queries formatting {table} into sql, with no results"""
        with SqliteCursor(self.conn) as cur:
            for querySql in querySqls:
                cur.execute(querySql.format(table=self.table))

    def getOidRange(self):
        """return half-open range of OIDs"""
        sql = "SELECT MIN(oid), MAX(oid)+1 FROM {table}"
        return next(self.query(sql, []), (0, 0))


class Sequence(namedtuple("Sequence",
                          ("name", "seq"))):
    """a short sequence, such as  RNA or protein"""
    __slots__ = ()

    def toFasta(self):
        """convert sequence to FASTA record, as a string, including newlines"""
        return ">{}\n{}\n".format(self.name, self.seq)


class SequenceDbTable(HgLiteTable):
    """
    Storage for short sequences (RNA or protein).
    """
    createSql = """CREATE TABLE {table} (
            name TEXT NOT NULL,
            seq TEXT NOT NULL);"""
    insertSql = """INSERT INTO {table} ({columns}) VALUES ({values});"""
    indexSql = """CREATE UNIQUE INDEX {table}_name ON {table} (name);"""

    columnNames = Sequence._fields

    def __init__(self, conn, table, create=False):
        super(SequenceDbTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        """create table"""
        self._create(self.createSql)

    def index(self):
        """create index after loading"""
        self._index(self.indexSql)

    def loads(self, rows):
        """load rows into table.  Each element of row is a list, tuple, or Sequence object of name and seq"""
        self._inserts(self.insertSql, self.columnNames, rows)

    def loadFastaFile(self, faFile):
        """load a FASTA file"""
        rows = [(faRec.id, str(faRec.seq))
                for faRec in SeqIO.parse(faFile, "fasta")]
        self.loads(rows)

    def names(self):
        """get generator over all names in table"""
        sql = "SELECT {columns} FROM {table};"
        for row in self.query(sql, ("name",)):
            yield row[0]

    def get(self, name):
        "retrieve a sequence by name, or None"
        sql = "SELECT name, seq FROM {table} WHERE name = ?;"
        row = next(self.query(sql, self.columnNames, name), None)
        if row is None:
            return None
        else:
            return Sequence(*row)

    def getByName(self, name):
        "get or error if not found"
        seq = self.get(name)
        if seq is None:
            raise PycbioException("can't find sequence {} in table {}".format(name, self.table))
        return seq

    def getRows(self, startOid, endOid):
        "generator for sequence for a range of OIDs (1/2 open)"
        sql = "SELECT {columns} FROM {table} WHERE (oid >= ?) AND (oid < ?)"
        return self.queryRows(sql, self.columnNames,
                              lambda cur, row: Sequence(name=row[0], seq=row[1]),
                              startOid, endOid)


class PslDbTable(HgLiteTable):
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
        super(PslDbTable, self).__init__(conn, table)
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
        return None if raw else lambda cur, row: Psl(row)

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
            if isinstance(strand, six.string_types):
                strand = [strand]
            sql += " AND (strand in ({}))".format(','.join(["'{}'".format(s) for s in strand]))
        if extraWhere is not None:
            sql += " AND ({})".format(extraWhere)
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw))


class GenePredDbTable(HgLiteTable):
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
        super(GenePredDbTable, self).__init__(conn, table)
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

    # FIXME: dups code above
    @staticmethod
    def _binGenePredRow(row):
        "add bin; note modifies row"
        row.insert(0, Binner.calcBin(int(row[3]), int(row[4])))
        return row

    def loadGenePredFile(self, genePredFile):
        """load a genePred file, adding bin"""
        rows = []
        for row in TabFileReader(genePredFile):
            rows.append(self._binGenePredRow(row))
        self.loadsWithBin(rows)

    @staticmethod
    def _getRowFactory(raw):
        return None if raw else lambda cur, row: GenePred(row)

    def getAll(self, raw=False):
        """Generator for all genePreds in a table.  If raw is
        specified, don't convert to GenePred objects if raw is True."""
        sql = "SELECT {columns} FROM {table}"
        return self.queryRows(sql, self.columnNames, self._getRowFactory(raw))

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


class GencodeAttrs(namedtuple("GencodeAttrs",
                              ("geneId", "geneName", "geneType", "geneStatus", "transcriptId",
                               "transcriptName", "transcriptType", "transcriptStatus", "havanaGeneId",
                               "havanaTranscriptId", "ccdsId", "level", "transcriptClass"))):
    """Attributes of a GENCODE transcript"""
    pass


class GencodeAttrsDbTable(HgLiteTable):
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
            transcriptClass TEXT NOT NULL)"""
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
    ]

    columnNames = GencodeAttrs._fields

    def __init__(self, conn, table, create=False):
        super(GencodeAttrsDbTable, self).__init__(conn, table)
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
        return [getattr(tsvRow, cn) for cn in self.columnNames]

    def loadTsv(self, attrsFile):
        """load a GENCODE attributes file, adding bin"""
        typeMap = {"geneStatus": noneIfEmpty,
                   "transcriptStatus": noneIfEmpty,
                   "havanaGeneId": noneIfEmpty,
                   "havanaTranscriptId": noneIfEmpty,
                   "ccdsId": noneIfEmpty,
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
    pass


class GencodeTranscriptSourceDbTable(HgLiteTable):
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
        super(GencodeTranscriptSourceDbTable, self).__init__(conn, table)
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
    pass


class GencodeTranscriptionSupportLevelDbTable(HgLiteTable):
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
        super(GencodeTranscriptionSupportLevelDbTable, self).__init__(conn, table)
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
    pass


class GencodeTagDbTable(HgLiteTable):
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
        super(GencodeTagDbTable, self).__init__(conn, table)
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
