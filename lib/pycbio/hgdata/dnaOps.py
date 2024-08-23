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

# odd: _strComplements is a dict wutg ints ints
#      _bytesComplements is a byte string, don't see how it works
# we just store ints
_ordValidBases = frozenset(_strComplements.keys())

def _dnaTypeError(dna):
    raise TypeError(f"DNA sequence must be str or bytes, got {type(dna)}")

def complement(dna):
    if isinstance(dna, str):
        return dna.translate(_strComplements)
    elif isinstance(dna, bytes):
        return dna.translate(_bytesComplements)
    else:
        _dnaTypeError(dna)

def reverseComplement(dna):
    "reverse complement a str of bytes of DNA sequences"
    return complement(dna)[::-1]

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

def isValidBase(base):
    assert len(base) == 1
    if isinstance(base, (str, bytes)):
        return ord(base) in _ordValidBases
    else:
        _dnaTypeError(base)
