# Copyright 2006-2012 Mark Diekhans
"""Module to access output of clusterGenes UCSC browser command"""

from collections import defaultdict
from pycbio.hgdata.autoSql import strArrayType
from pycbio.tsv import TsvReader


def cgBoolParse(val):
    if val == "y":
        return True
    elif val == "n":
        return False
    else:
        raise ValueError("expected y or n: " + val)


def cgBoolFormat(val):
    if val is True:
        return "y"
    elif val is False:
        return "n"
    else:
        raise ValueError("expected bool type, got: " + type(val))


cgBoolSpec = (cgBoolParse, cgBoolFormat)

# cluster	table	gene	chrom	txStart	txEnd	strand	hasExonConflicts	hasCdsConflicts	exonConflicts	cdsConflicts
# cluster	table	gene	chrom	txStart	txEnd	strand
typeMap = {
    "cluster": int,
    "txStart": int,
    "txEnd": int,
    "rnaLength": int,
    "cdsLength": int,
    "hasExonConflicts": cgBoolSpec,
    "hasCdsConflicts": cgBoolSpec,
    "exonConflicts": strArrayType,
    "cdsConflicts": strArrayType,
}


class Cluster(list):
    """one gene cluster, a list of genePred objects from file, A field
    clusterObj is added to each row that links back to this object"""
    def __init__(self, clusterId):
        self.clusterId = clusterId

        self.chrom = None
        self.start = None
        self.end = None
        self.strand = None
        self.tableSet = set()

        # set to None if conflicts were not collected
        self.hasExonConflicts = None
        self.hasCdsConflicts = None

    def add(self, row):
        self.append(row)
        row.clusterObj = self
        if (self.chrom is None):
            self.chrom = row.chrom
            self.start = row.txStart
            self.end = row.txEnd
            self.strand = row.strand
        else:
            self.start = min(self.start, row.txStart)
            self.end = max(self.end, row.txEnd)
        if "hasExonConflicts" in vars(row):
            self.hasExonConflicts = row.hasExonConflicts
            self.hasCdsConflicts = row.hasCdsConflicts
        self.tableSet.add(row.table)

    def getTableGenes(self, table):
        genes = None
        for g in self:
            if g.table == table:
                if genes is None:
                    genes = []
                genes.append(g)
        return genes

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)

    def write(self, fh, trackSet=None):
        "if trackSet is specified, only output genes in this set"
        for gene in self:
            if (trackSet is None) or (gene.table in trackSet):
                gene.write(fh)


class ClusterGenes(list):
    """Object to access output of ClusterGenes.  List of Cluster objects,
    indexed by clusterId.  Note that clusterId is one based, entry 0 is
    None, however generator doesn't return it or other Null clusters.
    """
    def __init__(self, clusterGenesOut):
        self.genes = defaultdict(list)
        self.tableSet = set()
        tsvRdr = TsvReader(clusterGenesOut, typeMap=typeMap)
        self.columns = tsvRdr.columns
        for gene in tsvRdr:
            self._addGene(gene)

    def haveCluster(self, clusterId):
        " determine if the specified cluster exists"
        if clusterId >= len(self):
            return False
        return self[clusterId] is not None

    def _getCluster(self, clusterId):
        while len(self) <= clusterId:
            self.append(None)
        if self[clusterId] is None:
            self[clusterId] = Cluster(clusterId)
        return self[clusterId]

    def _addGene(self, row):
        cluster = self._getCluster(row.cluster)
        cluster.add(row)
        self.genes[row.gene].append(row)
        self.tableSet.add(row.table)

    def __iter__(self):
        "get generator over non-null clusters"
        for cl in super(ClusterGenes, self).__iter__():
            if cl is not None:
                yield cl
