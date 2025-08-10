# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.gencode import biotypes, gencodeTags  # noqa:F401


def testGencodeBiotype():
    # asserts in biotypes do testing
    assert biotypes.BioType("ambiguous_orf") == biotypes.BioType.ambiguous_orf

def testGencodeBTags():
    assert gencodeTags.GencodeTag.CCDS not in gencodeTags.gencodeTagNotFullCds
