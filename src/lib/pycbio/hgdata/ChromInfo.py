"""
Object with chromosome information that can be loaded from a variety of
sources.
"""
# Copyright 2006-2012 Mark Diekhans
from pycbio.sys.procOps import callProc
from pycbio.tsv import TabFile

class ChromInfo(object):
    "object with chromosome information"
    def __init__(self, chrom, size):
        self.chrom = chrom
        self.size = size

class ChromInfoTbl(dict):
    "object to manage information about chromosomes"
    
    def __init__(self, chromClass=ChromInfo):
        self.chromClass = chromClass

    def __addRow(self, chrom, size):
        self[chrom] = self.chromClass(chrom, size)

    def loadChromSizes(self, chromSizes):
        "Load from chrom.sizes file"
        for row in TabFile(chromSizes):
            self.__addRow(row[0], int(row[1]))

    def loadChromInfoDb(self, conn):
        "Load from chomoInfo table"
        cur = conn.cursor()
        try:
            for row in cur.execute("select chrom, size from chromInfo"):
                self.__addRow(row[0], row[1])
        finally:
            cur.close()
