# Copyright 2006-2018 Mark Diekhans
"""
Storage of genome data in sqlite for use in cluster jobs and other random
access uses.
"""
from pycbio.db.sqliteOps import SqliteCursor

# FIXME: removed duplicated functions and move to base class or mix-in especially gencode
# FIXME: move generic sqlite to another module.
# FIXME: often hides sql too much (gencode_icedb/general/gencodeDb.py: getGeneIdsStartingInBounds)
# FIXME: maaybe a series of functions to build queryes would be the ticket (binning, in querys, ihserts); this is not that composable.
# FIXME" prefix generators with gen**********
# FIXME: term load is confusing, use read/get, write, or insert
# FIXME: maybe separate table definitions from query construction


def noneIfEmpty(s):
    return s if s != "" else None


class HgSqliteTable(object):
    """Base class for SQL list table interface object."""
    def __init__(self, conn, table):
        self.conn = conn
        self.table = table

    def _create(self, createSql):
        self.executes(["DROP TABLE IF EXISTS {table};".format(table=self.table),
                       createSql])

    def _index(self, indexSql):
        if isinstance(indexSql, (str, bytes)):
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
