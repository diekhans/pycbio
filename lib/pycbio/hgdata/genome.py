#!/usr/bin/env python3
# Copyright 2025-2025 Mark Diekhans
import re
from abc import ABC, abstractmethod
from pycbio import PycbioException
from pycbio.sys.symEnum import SymEnum

class GenomeFmt(SymEnum):
    """format of the genome sequence file"""
    fasta = 1
    twobit = 2
    guess = 3

class Genome(ABC):
    """Random access to genome sequences"""

    @abstractmethod
    def get_seq_ids(self):
        "return list of sequences ids"
        pass

    @abstractmethod
    def get_seq_length(self):
        "length of a sequence"
        pass

    @abstractmethod
    def get_seq(self, seq_id, start=None, end=None):
        "get a sequence or region of a sequence"
        pass

class _GenomeFasta(Genome):
    """Random access to samtools faidx FASTA genome sequences"""

    def __init__(self, fasta_file):
        import pysam  # lazy import
        self._fh = pysam.FastaFile(fasta_file)

    def get_seq_ids(self):
        return self._fh.references

    def get_seq_length(self, seq_id):
        return self._fh.get_reference_length(seq_id)

    def get_seq(self, seq_id, start=None, end=None):
        return self._fh.fetch(seq_id, start, end)

class _GenomeTwoBit(Genome):
    """Random access to UCSC two-bit genome sequences"""

    def __init__(self, twobit_file):
        from pytwobit import TwoBit  # lazy import
        self._fh = TwoBit(twobit_file)

    def get_seq_ids(self):
        return self._fh.references

    def get_seq_length(self, seq_id):
        return self._fh.get_reference_length(seq_id)

    def get_seq(self, seq_id, start=None, end=None):
        return self._fh.fetch(seq_id, start, end)


def genomeFactory(seq_file, *, fmt=GenomeFmt.guess):
    """create the genome reader for the format.  If guess is specified,
    determine file type from extension"""
    fasta_re = r".+\.(fa|fasta)(\.gz)?$"
    twobit_re = r".+\.2bit$"
    if fmt is GenomeFmt.fasta:
        return _GenomeFasta(seq_file)
    elif fmt is GenomeFmt.twobit:
        return _GenomeTwoBit(seq_file)
    elif fmt is GenomeFmt.guess:
        if re.match(fasta_re, seq_file):
            return _GenomeFasta(seq_file)
        elif re.match(twobit_re, seq_file):
            return _GenomeTwoBit(seq_file)
        else:
            raise PycbioException(f"can not determine genome file type for `{seq_file}'")
