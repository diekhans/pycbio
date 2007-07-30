from pycbio.tsv.TabFile import TabFile

class ChromSize(object):
    "object with chromosome information"
    def __init__(self, chrom, size):
        self.chrom = chrom
        self.size = size

class ChromSizes(dict):
    "object to manage information about chromosomes"
    
    def __init__(self, chromSizesFile):
        for row in TabFile(chromSizesFile):
            cs = ChromSize(row[0], int(row[1]))
            self[cs.chrom] = cs
