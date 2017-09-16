"""
Object with chromosome information that can be loaded from a variety of
sources.
"""
# Copyright 2006-2012 Mark Diekhans
from __future__ import print_function
from pycbio.tsv import TabFile


class ChromInfo(object):
    "object with chromosome information"
    def __init__(self, chrom, size):
        self.chrom = chrom
        self.size = size

    def __str__(self):
        return self.chrom + " " + str(self.size)


class ChromInfoTbl(dict):
    "object to manage information about chromosomes"

    def __init__(self, chromSizes=None, conn=None, chromClass=ChromInfo):
        "loads from either chromSizes file or database conn 2chromInfo table"
        self.chromClass = chromClass
        if chromSizes is not None:
            self.loadChromSizes(chromSizes)
        elif conn is not None:
            self.loadChromInfoDb(conn)

    def __addRow(self, chrom, size):
        self[chrom] = self.chromClass(chrom, size)

    def loadChromSizes(self, chromSizes):
        "Load from chrom.sizes file"
        for row in TabFile(chromSizes):
            self.__addRow(row[0], int(row[1]))

    def loadChromInfoDb(self, conn):
        "Load from chromoInfo table"
        cur = conn.cursor()
        try:
            cur.execute("select chrom, size from chromInfo")
            for row in cur:
                self.__addRow(row[0], row[1])
        finally:
            cur.close()
