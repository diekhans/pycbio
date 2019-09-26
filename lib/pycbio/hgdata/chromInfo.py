"""
Object with chromosome information that can be loaded from a variety of
sources.
"""
# Copyright 2006-2012 Mark Diekhans
from collections import namedtuple
from pycbio.tsv import TabFile

class ChromInfo(namedtuple("chromInfo",
                           ("chrom", "size"))):
    "object with chromosome information"

    def __str__(self):
        return "{chrom}\t{size}".format(self)


class ChromInfoTbl(dict):
    """object to manage information about chromosomes, indexed by chrom name"""

    def _addRow(self, chrom, size):
        self[chrom] = ChromInfo(chrom, size)

    @staticmethod
    def loadFile(chromSizes):
        "Load from chrom.sizes file"
        chroms = ChromInfoTbl()
        for row in TabFile(chromSizes):
            chroms._addRow(row[0], int(row[1]))
        return chroms

    @staticmethod
    def loadDb(conn):
        "Load from chromoInfo table"
        chroms = ChromInfoTbl()
        cur = conn.cursor()
        try:
            cur.execute("SELECT chrom, size FROM chromInfo")
            for row in cur:
                chroms._addRow(row[0], int(row[1]))
        finally:
            cur.close()
        return chroms
