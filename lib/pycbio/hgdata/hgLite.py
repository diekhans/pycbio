# Copyright 2006-2016 Mark Diekhans
"""
Storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
from collections import namedtuple
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.genePred import GenePred
from pycbio.tsv import TabFileReader
from pycbio.hgdata.rangeFinder import Binner
from Bio import SeqIO

# FIXME: HgLiteTable could become wrapper around a connection,
# and make table operations functions.???  probably not


def sqliteHaveTable(conn, table):
    "check if a table exists"
    sql = """SELECT count(*) FROM sqlite_master WHERE type="table" AND name=?;"""
    cur = conn.cursor()
    try:
        cur.execute(sql, (table, ))
        row = next(cur)
        return row[0] > 0
    finally:
        cur.close()


class HgLiteTable(object):
    """Base class for SQL list table interface object"""
    def __init__(self, conn, table):
        self.conn = conn
        self.table = table

    def _create(self, createSql):
        self.executes(["DROP TABLE IF EXISTS {table};".format(table=self.table),
                       createSql])

    def _index(self, indexSql):
        if isinstance(indexSql, str):
            indexSql = [indexSql]
        with self.conn:
            self.executes(indexSql)

    @staticmethod
    def _joinColNames(columns):
        return ",".join(columns)

    @staticmethod
    def _makeValueTokens(columns):
        "generate `?' for insert values"
        return ",".join(len(columns) * ["?"])

    def __formatSql(self, sql, columns):
        "format {table}, {columns}, and if in sql, {values}"
        return sql.format(table=self.table,
                          columns=self._joinColNames(columns),
                          values=self._makeValueTokens(columns))
    
    def _insert(self, insertSql, columns, row):
        """insert a row, formatting {table}, {columns}, {values} into sql"""
        with self.conn:
            self.conn.execute(self.__formatSql(insertSql, columns), row)

    def _inserts(self, insertSql, columns, rows):
        """insert multiple rows, formatting {table}, {columns}, {values} into sql"""
        with self.conn:
            self.conn.executemany(self.__formatSql(insertSql, columns), rows)

    def queryRows(self, querySql, columns, rowFactory, *queryargs):
        """run query, formatting {table}, {columns} into sql and generator over results and
        setting row factory"""
        with self.conn:
            cur = self.conn.cursor()
            cur.row_factory = rowFactory
            try:
                sql = querySql.format(table=self.table, columns=self._joinColNames(columns))
                cur.execute(sql, queryargs)
                for row in cur:
                    yield row
            finally:
                cur.close()

    def query(self, querySql, columns, *queryargs):
        """run query, formatting {table} into sql and generator over results"""
        return self.queryRows(querySql, columns, None, *queryargs)

    def execute(self, querySql):
        """execute a query formatting {table} into sql, with no results"""
        with self.conn:
            cur = self.conn.cursor()
            try:
                cur.execute(query.format(table=self.table))
            finally:
                cur.close()

    def executes(self, querySqls):
        """execute multiple queries formatting {table} into sql, with no results"""
        with self.conn:
            cur = self.conn.cursor()
            try:
                for querySql in querySqls:
                    cur.execute(querySql.format(table=self.table))
            finally:
                cur.close()

    def getOidRange(self):
        """return half-open range of OIDs"""
        columns = ("min(oid)", "max(oid)+1")
        sql = "select {columns} from {table}"
        return next(self.query(sql, columns), (0, 0))


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
    __createSql = """CREATE TABLE {table} (
            name text not null,
            seq text not null);"""
    __insertSql = """INSERT INTO {table} (name, seq) VALUES (?, ?);"""
    __indexSql = """CREATE UNIQUE INDEX {table}_name on {table} (name);"""

    columnNames = ("name", "seq")
    
    def __init__(self, conn, table, create=False):
        super(SequenceDbTable, self).__init__(conn, table)
        if create:
            self.create()

    def create(self):
        """create table"""
        self._create(self.__createSql)

    def index(self):
        """create index after loading"""
        self._index(self.__indexSql)

    def loads(self, rows):
        """load rows into table.  Each element of row is a list, tuple, or Sequence object of name and seq"""
        self._inserts(self.__insertSql, self.columnNames, rows)

    def loadFastaFile(self, faFile):
        """load a FASTA file"""
        rows = []
        for faRec in SeqIO.parse(faFile, "fasta"):
            rows.append((faRec.id, str(faRec.seq)))
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
            raise Exception("can't find sequence {} in table {}".format(name, self.table))
        return seq

    def getRows(self, startOid, endOid):
        "generator for sequence for a range of OIDs (1/2 open)"
        sql = "select {columns} from {table} where (oid >= ?) and (oid < ?)"
        return self.queryRows(sql, self.columnNames,
                              lambda cur, row: Sequence(name=row[0], seq=row[1]),
                              startOid, endOid)


class PslDbTable(HgLiteTable):
    """
    Storage for PSL alignments.  Psl objects, or raw sql rows can be
    return.  Raw return is to save object creation overhead when results are
    going to be written to a file.
    """
    __createSql = """CREATE TABLE {table} (
            bin int unsigned not null,
            matches int unsigned not null,
            misMatches int unsigned not null,
            repMatches int unsigned not null,
            nCount int unsigned not null,
            qNumInsert int unsigned not null,
            qBaseInsert int unsigned not null,
            tNumInsert int unsigned not null,
            tBaseInsert int unsigned not null,
            strand text not null,
            qName text not null,
            qSize int unsigned not null,
            qStart int unsigned not null,
            qEnd int unsigned not null,
            tName text not null,
            tSize int unsigned not null,
            tStart int unsigned not null,
            tEnd int unsigned not null,
            blockCount int unsigned not null,
            blockSizes blob not null,
            qStarts blob not null,
            tStarts blob not null)"""
    __indexSql = [
        """CREATE INDEX {table}_tName_bin on {table} (tName, bin)""",
        """CREATE INDEX {table}_qname on {table} (qName)"""]

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
        self._create(self.__createSql)

    def index(self):
        """create index after loading"""
        self._index(self.__indexSql)

    def loadsWithBin(self, binnedRows):
        """load PSLs rows which already have bin column"""
        sql = "INSERT INTO {table} ({columns}) VALUES ({values});"
        self._inserts(sql, self.columnNamesBin, binnedRows)

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
    def __binPslRow(row):
        "add bin; note modifies row"
        row.insert(0, Binner.calcBin(int(row[15]), int(row[16])))
        return row

    def loadPslFile(self, pslFile):
        """load a PSL file, adding bin"""
        rows = []
        for row in TabFileReader(pslFile):
            rows.append(self.__binPslRow(row))
        self.loadsWithBin(rows)

    @staticmethod
    def __getRowFactory(raw):
        return None if raw else lambda cur, row: Psl(row)

    def getByQName(self, qName, raw=False):
        """get list of Psl objects (or raw rows) for all alignments for qName """
        sql = "select {columns} from {table} where qName = ?"
        return list(self.queryRows(sql, self.columnNames, self.__getRowFactory(raw), qName))

    def getRows(self, startOid, endOid, raw=False):
        """generator for PSLs for a range of OIDs (1/2 open).  If raw is
        specified, don't convert to Psl objects if raw is True"""
        sql = "select {columns} from {table} where (oid >= ?) and (oid < ?)"
        return self.queryRows(sql, self.columnNames, self.__getRowFactory(raw), startOid, endOid)

    def getTRangeOverlap(self, tName, tStart, tEnd, raw=False):
        """Get alignments overlapping tRange  If raw is
        specified, don't convert to Psl objects if raw is True."""
        binWhere = Binner.getOverlappingSqlExpr("bin", "tName", "tStart", "tEnd", tName, tStart, tEnd)
        sql = "select {{columns}} from {{table}} where {};".format(binWhere)
        return self.queryRows(sql, self.columnNames, self.__getRowFactory(raw))


class GenePredDbTable(HgLiteTable):
    """
    Storage for genePred annotations.  GenePred  objects, or raw sql rows can beg38
    return.  Raw return is to save object creation overhead when results are
    going to be written to a file.
    """
    __createSql = """CREATE TABLE {table} (
            bin int unsigned not null,
            name text not null,
            chrom text not null,
            strand char not null,
            txStart int unsigned not null,
            txEnd int unsigned not null,
            cdsStart int unsigned not null,
            cdsEnd int unsigned not null,
            exonCount int unsigned not null,
            exonStarts blob not null,
            exonEnds blob not null,
            score int default null,
            name2 text not null,
            cdsStartStat text not null,
            cdsEndStat text not null,
            exonFrames blob not null)"""
    __indexSql = [
        """CREATE INDEX {table}_chrom_bin on {table} (chrom, bin)""",
        """CREATE INDEX {table}_name on {table} (name)"""]

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
        self._create(self.__createSql)

    def index(self):
        """create index after loading"""
        self._index(self.__indexSql)

    def loadsWithBin(self, binnedRows):
        """load genePred rows which already have bin column"""
        sql = "INSERT INTO {table} ({columns}) VALUES ({values});"
        self._inserts(sql, self.columnNamesBin, binnedRows)

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
    def __binGenePredRow(row):
        "add bin; note modifies row"
        row.insert(0, Binner.calcBin(int(row[3]), int(row[4])))
        return row

    def loadGenePredFile(self, genePredFile):
        """load a genePred file, adding bin"""
        rows = []
        for row in TabFileReader(genePredFile):
            rows.append(self.__binGenePredRow(row))
        self.loadsWithBin(rows)

    @staticmethod
    def __getRowFactory(raw):
        return None if raw else lambda cur, row: GenePred(row)

    def getByName(self, name, raw=False):
        """get list of GenePred objects (or raw rows) for all alignments for name """
        sql = "select {columns} from {table} where name = ?"
        return list(self.queryRows(sql, self.columnNames, self.__getRowFactory(raw), name))

    def getRows(self, startOid, endOid, raw=False):
        """generator for genePreds for a range of OIDs (1/2 open).  If raw is
        specified, don't convert to GenePred objects if raw is True."""
        sql = "select {columns} from {table} where (oid >= ?) and (oid < ?)"
        return self.queryRows(sql, self.columnNames, self.__getRowFactory(raw), startOid, endOid)

    def getRangeOverlap(self, chrom, start, end, raw=False):
        """Get alignments overlapping range  If raw is
        specified. Don't convert to GenePred objects if raw is True."""
        binWhere = Binner.getOverlappingSqlExpr("bin", "chrom", "txStart", "txEnd", chrom, start, end)
        sql = "select {{columns}} from {{table}} where {};".format(binWhere)
        return self.queryRows(sql, self.columnNames, self.__getRowFactory(raw))