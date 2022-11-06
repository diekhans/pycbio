# Copyright 2006-2022 Mark Diekhans
"""
Read genePreds from mysql queries.
"""
from pycbio.hgdata.genePred import genePredFromDictRow
from pycbio.db import mysqlOps


class GenePredMySqlReader(object):
    """Read genePreds from a mysql query"""
    def __init__(self, conn, query, queryArgs=None):
        self.conn = conn
        self.query = query
        self.queryArgs = queryArgs

    def __iter__(self):
        cur = self.conn.cursor(cursorclass=mysqlOps.DictCursor)
        try:
            cur.execute(self.query, self.queryArgs)
            for row in cur:
                yield genePredFromDictRow(row)
        finally:
            cur.close()
