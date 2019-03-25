# Copyright 2006-2018 Mark Diekhans
"""
Read genePreds from mysql queries.
"""
from pycbio.db import mysqlOps
from pycbio.hgdata.genePred import GenePred


class GenePredMySqlReader(object):
    """Read genePreds from a mysql query"""
    def __init__(self, conn, query, queryArgs=None):
        self.conn = conn
        self.query = query
        self.queryArgs = queryArgs

    def __iter__(self):
        cur = self.conn.cursor()
        try:
            cur.execute(self.query, self.queryArgs)
            colIdxMap = mysqlOps.cursorColIdxMap(cur)
            for row in cur:
                yield GenePred(row, dbColIdxMap=colIdxMap)
        finally:
            cur.close()
