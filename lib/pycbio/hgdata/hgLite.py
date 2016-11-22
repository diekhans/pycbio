# Copyright 2006-2016 Mark Diekhans
"""
Storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
import sqlite3
from collections import namedtuple
from pycbio.hgdata.psl import Psl
from pycbio.tsv import TabFileReader
from pycbio.hgdata.rangeFinder import Binner
from Bio import SeqIO

# FIXME: HgLiteTable could become wrapper around a connection,
# and make table operations functions.?

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

    def _insert(self, insertSql, row):
        """insert a row, formatting table name"""
        with self.conn:
            self.conn.execute(insertSql.format(table=self.table), row)

    def _inserts(self, insertSql, rows):
        """insert multiple rows, formatting table name"""
        with self.conn:
            self.conn.executemany(insertSql.format(table=self.table), rows)

    def queryRows(self, query, rowFactory, *queryargs):
        """run query, formatting table name and generator over results and
        setting row factory"""
        with self.conn:
            cur = self.conn.cursor()
            cur.row_factory = rowFactory
            try:
                cur.execute(query.format(table=self.table), queryargs)
                for row in cur:
                    yield row
            finally:
                cur.close()

    def query(self, query, *queryargs):
        """run query, formatting table name and generator over results"""
        return self.queryRows(query, None, *queryargs)

    def execute(self, query):
        """execute a query formatting table name, with no results"""
        with self.conn:
            cur = self.conn.cursor()
            try:
                cur.execute(query.format(table=self.table))
            finally:
                cur.close()

    def executes(self, queries):
        """execute multiple queries formatting table name, with no results"""
        with self.conn:
            cur = self.conn.cursor()
            try:
                for query in queries:
                    cur.execute(query.format(table=self.table))
            finally:
                cur.close()

    def getOidRange(self):
        """return half-open range of OIDs"""
        sql = "select min(oid), max(oid)+1 from {}".format(self.table)
        return next(self.query(sql), (0, 0))


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
        self._inserts(self.__insertSql, rows)

    def loadFastaFile(self, faFile):
        """load a FASTA file"""
        rows = []
        for faRec in SeqIO.parse(faFile, "fasta"):
            rows.append((faRec.id, str(faRec.seq)))
        self.loads(rows)

    def names(self):
        """get generator over all names in table"""
        sql = "SELECT name FROM {table};"
        for row in self.query(sql):
            yield row[0]

    def get(self, name):
        "retrieve a sequence by name, or None"
        sql = "SELECT name, seq FROM {table} WHERE name = ?;"
        row = next(self.query(sql, name), None)
        if row is None:
            return None
        else:
            return Sequence(*row)

    def getRows(self, startOid, endOid):
        "generator for sequence for a range of OIDs (1/2 open)"
        sql = "select name, seq from {table} where (oid >= ?) and (oid < ?)"
        return self.queryRows(sql, lambda cur, row: Sequence(name=row[0], seq=row[1]),
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
            qStarts text not null,
            tStarts text not null)"""
    __indexSql = [
        """CREATE INDEX {table}_tName_bin on {table} (tName, bin)""",
        """CREATE INDEX {table}_qname on {table} (qName)"""]

    # doesn't include bin
    columnsNamesSql = """matches, misMatches, repMatches, nCount, qNumInsert, qBaseInsert, tNumInsert,
    tBaseInsert, strand, qName, qSize, qStart, qEnd, tName, tSize, tStart, tEnd,
    blockCount, blockSizes, qStarts, tStarts"""

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
        sql = "INSERT INTO {{table}} (bin, {}) VALUES ({});".format(self.columnsNamesSql, ",".join(22 * ["?"]))
        self._inserts(sql, binnedRows)

    def loads(self, rows):
        """load rows, which can be list-like or Psl objects, adding bin"""
        binnedRows = []
        for row in rows:
            if isinstance(row, Psl):
                row = row.toRow()
            bin = Binner.calcBin(int(row[15]), int(row[16]))
            binnedRows.append((bin,) + tuple(row))
        self.loadsWithBin(binnedRows)

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
        sql = "select {} from {{table}} where qName = ?".format(self.columnsNamesSql)
        return list(self.queryRows(sql, self.__getRowFactory(raw), qName))

    def getRows(self, startOid, endOid, raw=False):
        """generator for PSLs for a range of OIDs (1/2 open).  If raw is
        specified, don't convert to Psl objects."""
        sql = "select {} from {} where (oid >= ?) and (oid < ?)".format(self.columnsNamesSql, self.table)
        return self.queryRows(sql, self.__getRowFactory(raw), startOid, endOid)

    def getTRangeOverlap(self, tName, tStart, tEnd, raw=False):
        """Get alignments overlapping tRange  If raw is
        specified, don't convert to Psl objects."""
        sql = "select {} from {{table}} where {};".format(self.columnsNamesSql,
                                                          Binner.getOverlappingSqlExpr("bin", "tName", "tStart", "tEnd", tName, tStart, tEnd))
        return self.queryRows(sql, self.__getRowFactory(raw))
