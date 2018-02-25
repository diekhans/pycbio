"""
Operations on strings of DNA sequences
"""
import six
from pycbio.sys import PycbioException
if six.PY2:
    import string
    maketrans = string.maketrans
else:
    maketrans = str.maketrans

##
# from: http://edwards.sdsu.edu/labsite/index.php/robs/396-reverse-complement-dna-sequences-in-python
##
_complements = maketrans('acgtrymkbdhvACGTRYMKBDHV',
                         'tgcayrkmvhdbTGCAYRKMVHDB')


def reverseComplement(dna):
    "reverse complement a string of DNA"
    if dna is None:
        return None
    else:
        return dna.translate(_complements)[::-1]


def reverseCoords(start, end, size):
    "reverse coordinate pair"
    return (size - end, size - start)


def reverseStrand(strand):
    "get reverse strand, or None if none"
    if strand is None:
        return None
    elif strand == '+':
        return '-'
    elif strand == '-':
        return '+'
    else:
        raise PycbioException("invalid strand '{}'".format(strand))
