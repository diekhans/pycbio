# Copyright 2006-2012 Mark Diekhans
""" classes for accesssing NCBI taxonomy data dumps from:
        ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_readme.txt
        ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
"""
import sys
from collections import defaultdict
from pycbio.sys import fileOps


class DmpFileParser(object):
    "parse one of the taxon dmp files"
    def __init__(self, dmpFile):
        self.dmpFile = dmpFile

    def __iter__(self):
        with fileOps.FileAccessor(self.dmpFile) as fh:
            for line in fh:
                # this leaves a last word with 'scientific name\t|\n'
                row = line.split("\t|\t")
                last = len(row) - 1
                row[last] = row[last].strip("\t|\n")
                yield row


class Node(object):
    "A record from nodes.dmp table"
    def __init__(self, row):
        self.taxId = int(row[0])
        self.parentTaxId = int(row[1])
        self.rank = sys.intern(row[2])
        self.emblCode = sys.intern(row[3])
        self.divisionId = int(row[4])
        self.inheritedDivFlag = bool(row[5])
        self.geneticCodeId = int(row[6])
        self.inheritedGCflag = bool(row[7])
        self.mitochondrialGeneticCodeId = int(row[8])
        self.inheritedMGCflag = bool(row[9])
        self.genBankHiddenFlag = bool(row[10])
        self.hiddenSubtreeRootFlag = bool(row[11])
        self.comments = row[12]


class Name(object):
    "A record from the names.dmp table"
    def __init__(self, row):
        self.taxId = int(row[0])
        self.nameTxt = sys.intern(row[1])
        self.uniqueName = sys.intern(row[2])
        self.nameClass = sys.intern(row[3])


class Tree(object):
    def _loadNames(self, dmpDir):
        self.names = defaultdict(list)
        self.sciNames = dict()
        sciName = "scientific name"

        for row in DmpFileParser(dmpDir + "/names.dmp"):
            name = Name(row)
            self.names[name.taxId].append(name)
            if name.nameClass == sciName:
                self.sciNames[name.nameTxt] = name.taxId

    def _loadNodes(self, dmpDir):
        self.nodes = dict()
        self.parentNodeRefs = defaultdict(list)
        for row in DmpFileParser(dmpDir + "/nodes.dmp"):
            node = Node(row)
            self.nodes[node.taxId] = node
            self.parentNodeRefs.append(node.parentTaxId, node)

    def __init__(self, dmpDir):
        "parse *.dmp files in dmpDir"
        self._loadNames(dmpDir)
        self._loadNodes(dmpDir)
