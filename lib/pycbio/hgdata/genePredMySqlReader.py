# Copyright 2006-2018 Mark Diekhans
"""
Read genePreds from mysql queries.
"""
from pycbio.db import mysqlOps
from pycbio.genePred import GenePred


class GenePredDbReader(object):
    """Read genePreds from a mysql query"""
    def __init__(self, conn, query, queryArgs=None):
        cur = conn.cursor()
        try:
            cur.execute(query, queryArgs)
            colIdxMap = mysqlOps.cursorColIdxMap(cur)
            for row in cur:
                yield GenePred(row, dbColIdxMap=colIdxMap)
        finally:
            cur.close()
