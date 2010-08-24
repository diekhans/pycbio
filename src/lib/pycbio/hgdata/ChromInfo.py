# Copyright 2006-2010 Mark Diekhans
from pycbio.sys.procOps import callProc

class ChromInfo(object):
    "object with chromosome information"
    def __init__(self, chrom, size):
        self.chrom = chrom
        self.size = size

class ChromInfoTbl(dict):
    "object to manage information about chromosomes"
    
    def __init__(self, db=None, nibDir=None):
        if (db == None) and (nibDir == None):
            raise Exception("must specify either db= or nibDir= arguments")
        self.db = db
        self.nibDir = nibDir
        if self.nibDir == None:
            self.nibDir = callProc(("genomeFind", db))

    def _loadChrom(self, chrom):
        "lazy loading of chromosome info"
        nib = self.nibDir + "/" + chrom + ".nib"
        line = callProc(["nibSize", nib])
        cols = line.split("\t")
        self[chrom] = ChromInfo(chrom, int(cols[2]))
        
    def __getitem__(self, chrom):
        "get the ChromInfo object for a chrom"
        if not chrom in self:
            self._loadChrom(chrom)
        return self.get(chrom)
