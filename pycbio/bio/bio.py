"""
Basic biology related functions
"""
import string


def convert_strand(s):
    """
    Given a potential strand value, converts either from True/False/None
    to +/-/None depending on value
    """
    assert s in [True, False, None, "+", "-", "."]
    if s is True:
        return "+"
    elif s is False:
        return "-"
    elif s is None:
        return "."
    elif s == "-":
        return False
    elif s == "+":
        return True
    elif s == ".":
        return None


def complement(seq, comp=string.maketrans("ATGCatgc", "TACGtacg")):
    """
    given a sequence, return the complement.
    """
    return str(seq).translate(comp)


def reverse_complement(seq):
    """
    Given a sequence, return the reverse complement.
    """
    return complement(seq)[::-1]
