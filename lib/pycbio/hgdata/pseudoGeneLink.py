# Copyright 2006-2012 Mark Diekhans
""" Object to load PseudoGeneLink table"""

# FIXME: this has never been used, maybe drop"
from pycbio.tsv.tsvTable import TsvTable
from pycbio.hgdata.autoSql import intArrayType


class PseudoGeneLink(TsvTable):
    """Tsv of PseudoGeneLink table"""

    _typeMap = {"chrom": str, "name": str, "strand": str,
                "blockSizes": intArrayType,
                "chromStarts": intArrayType,
                "type": str,
                "gChrom": str, "gStrand": str,
                "intronScores": intArrayType,
                "refSeq": str, "mgc": str, "kgName": str,
                "overName": str, "overStrand": str,
                "adaBoost": float, "posConf": float, "negConf": float}

    def __init__(self, pglFile):
        super(PseudoGeneLink, self).__init__(pglFile, multiKeyCols="name", typeMap=PseudoGeneLink._typeMap, defaultColType=int)

    def getNameIter(self, name):
        """get iter over rows for name"""
        return iter(list(self.indices.name.keys()))
