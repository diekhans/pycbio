"""
Operations on strings of DNA sequences
"""
from pycbio import PycbioException


##
# from: http://edwards.sdsu.edu/labsite/index.php/robs/396-reverse-complement-dna-sequences-in-python
##
_strComplements = str.maketrans('acgtrymkbdhvACGTRYMKBDHV',
                                'tgcayrkmvhdbTGCAYRKMVHDB')
_bytesComplements = bytes.maketrans(b'acgtrymkbdhvACGTRYMKBDHV',
                                    b'tgcayrkmvhdbTGCAYRKMVHDB')


def reverseComplement(dna):
    "reverse complement a str of bytes of DNA sequences"
    if dna is None:
        return None
    elif isinstance(dna, str):
        return dna.translate(_strComplements)[::-1]
    elif isinstance(dna, bytes):
        return dna.translate(_bytesComplements)[::-1]
    else:
        raise TypeError(f"DNA sequence must be str or bytes, got {type(dna)}")

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
