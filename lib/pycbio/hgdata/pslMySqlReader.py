"""
Read PSL from mysql queries.
"""
from pycbio.hgdata.psl import Psl
from pycbio.hgdata.rangeFinder import Binner


class PslMySqlReader(object):
    """Read PSLs from db query.  Factory methods are provide
    to generate instances for range queries."""

    pslColumns = ("matches", "misMatches", "repMatches", "nCount", "qNumInsert", "qBaseInsert", "tNumInsert", "tBaseInsert", "strand", "qName", "qSize", "qStart", "qEnd", "tName", "tSize", "tStart", "tEnd", "blockCount", "blockSizes", "qStarts", "tStarts")
    pslSeqColumns = ("qSequence", "tSequence")

    def __init__(self, conn, query, queryArgs=()):
        self.conn = conn
        self.query = query
        self.queryArgs = queryArgs

    def __iter__(self):
        cur = self.conn.cursor()
        try:
            cur.execute(self.query, self.queryArgs)
            for row in cur:
                yield Psl.fromDictRow(row)
        finally:
            cur.close()

    @staticmethod
    def targetRangeQuery(conn, table, tName, tStart, tEnd, haveSeqs=False):
        """ factor to generate PslMySqlReader for querying a target range.  Must have a bin column"""
        query = "select " + ",".join(PslMySqlReader.pslColumns)
        if haveSeqs:
            query += "," + ",".join(PslMySqlReader.pslSeqColumns)
        query += " from " + table + " where " \
            + Binner.getOverlappingSqlExpr("bin", "tName", "tStart", "tEnd", tName, tStart, tEnd)
        return PslMySqlReader(conn, query)
