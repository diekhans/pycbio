# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.hgdata import dnaOps

def testRevCmplStr():
    testSeq = "cgcggccatttgtctctt"
    rcSeq = dnaOps.reverseComplement(testSeq)
    assert rcSeq == "aagagacaaatggccgcg"

def testRevCmplBytes():
    testSeq = b"cgcggccatttgtctctt"
    rcSeq = dnaOps.reverseComplement(testSeq)
    assert rcSeq == b"aagagacaaatggccgcg"

def testIsValidStr():
    assert dnaOps.isValidBase('a')
    assert dnaOps.isValidBase('C')
    assert not dnaOps.isValidBase('@')

def testIsValidByte():
    assert dnaOps.isValidBase(b'a')
    assert dnaOps.isValidBase(b'C')
    assert not dnaOps.isValidBase(b'@')
