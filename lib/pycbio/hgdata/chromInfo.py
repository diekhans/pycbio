"""
Object with chromosome information that can be loaded from a variety of
sources.
"""
# Copyright 2006-2012 Mark Diekhans
from collections import namedtuple
from pycbio.sys import fileOps
from pycbio.db import mysqlOps
import pipettor

class ChromInfo(namedtuple("chromInfo",
                           ("chrom", "size"))):
    "object with chromosome information"

    def __str__(self):
        return f"{self.chrom}\t{self.size}"


class ChromInfoTbl(dict):
    """object to manage information about chromosomes, indexed by chrom name"""

    def _addRow(self, chrom, size):
        self[chrom] = ChromInfo(chrom, size)

    @staticmethod
    def loadFile(chromSizes):
        "Load from chrom.sizes file"
        chroms = ChromInfoTbl()
        for row in fileOps.iterRows(chromSizes):
            chroms._addRow(row[0], int(row[1]))
        return chroms

    @staticmethod
    def loadDb(conn):
        "Load from chromoInfo table"
        chroms = ChromInfoTbl()
        cur = conn.cursor(cursorclass=mysqlOps.DictCursor)
        try:
            cur.execute("SELECT chrom, size FROM chromInfo")
            for row in cur:
                chroms._addRow(row['chrom'], int(row['size']))
        finally:
            cur.close()
        return chroms

    @staticmethod
    def loadTwoBit(twoBitFile):
        "Load from twoBit file"
        chroms = ChromInfoTbl()
        with pipettor.Popen(["twoBitInfo", twoBitFile, "/dev/stdout"]) as fh:
            for row in fileOps.iterRows(fh):
                chroms._addRow(row[0], int(row[1]))
        return chroms
