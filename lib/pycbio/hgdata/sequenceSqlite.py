# Copyright 2006-2018 Mark Diekhans
"""
Storage of sequence tables in sqlite for use in cluster jobs and other
random access uses.
"""
from pycbio.hgdata.hgSqlite import HgSqliteTable
from collections import namedtuple
from pycbio.sys import PycbioException
from Bio import SeqIO


class Sequence(namedtuple("Sequence",
                          ("name", "seq"))):
    """a short sequence, such as  RNA or protein"""
    __slots__ = ()

    def toFasta(self):
        """convert sequence to FASTA record, as a string, including newlines"""
        return ">{}\n{}\n".format(self.name, self.seq)


class SequenceSqliteTable(HgSqliteTable):
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
        super(SequenceSqliteTable, self).__init__(conn, table)
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

    def getByOid(self, startOid, endOid):
        "generator for sequence for a range of OIDs (1/2 open)"
        sql = "SELECT {columns} FROM {table} WHERE (oid >= ?) AND (oid < ?)"
        return self.queryRows(sql, self.columnNames,
                              lambda cur, row: Sequence(name=row[0], seq=row[1]),
                              startOid, endOid)
