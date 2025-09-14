# Copyright 2025-2025 Mark Diekhans
import sys
import os.path as osp
import pytest

sys.path = ["../../../../lib", "../.."] + sys.path
import pycbio.sys.testingSupport as ts
from pycbio.hgdata.genome import genomeFactory

COMMON_OUTPUT_DIR = "../../../common-output"
GRCH38_FA = "grch38-regions.fa.gz"
GRCH38_TWOBIT = "grch38-regions.fa.gz"

def _get_genome_file(request, file_name):
    return osp.join(ts.get_test_dir(request), COMMON_OUTPUT_DIR, file_name)

def _get_genome(request, file_name):
    return genomeFactory(_get_genome_file(request, file_name))

@pytest.mark.parametrize("genome_file",
                         [GRCH38_FA, GRCH38_TWOBIT])
def test_genome_seq_ids(request, genome_file):
    genome = _get_genome(request, genome_file)
    assert genome.get_seq_ids() == ["chr19_51887540_51906200"]

@pytest.mark.parametrize("genome_file",
                         [GRCH38_FA, GRCH38_TWOBIT])
def test_genome_seq_length(request, genome_file):
    genome = _get_genome(request, genome_file)
    assert genome.get_seq_length("chr19_51887540_51906200") == 18660

@pytest.mark.parametrize("genome_file",
                         [GRCH38_FA, GRCH38_TWOBIT])
def test_genome_seq(request, genome_file):
    genome = _get_genome(request, genome_file)
    assert genome.get_seq("chr19_51887540_51906200", 100, 128) == 'CCAAGCACTGGTTCCAATGCGGAGACCA'
