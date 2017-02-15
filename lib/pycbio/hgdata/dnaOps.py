"""
Operations on strings of DNA sequences
"""
import string

##
# from: http://edwards.sdsu.edu/labsite/index.php/robs/396-reverse-complement-dna-sequences-in-python
##
_complements = string.maketrans('acgtrymkbdhvACGTRYMKBDHV',
                                'tgcayrkmvhdbTGCAYRKMVHDB')


def reverseComplement(dna):
    "reverse complement a string of DNA"
    if dna is None:
        return None
    else:
        return dna.translate(_complements)[::-1]
