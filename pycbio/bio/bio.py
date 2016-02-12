"""
Basic biology related functions
"""
import string
import os
from pyfasta import Fasta, NpyFastaRecord


class UpperNpyFastaRecord(NpyFastaRecord):
    """
    Used when we want only upper case records.
    If as_string is False, will no longer return a memmap object but instead a list.
    """
    def __getitem__(self, islice):
        d = self.getdata(islice)
        return d.tostring().decode().upper() if self.as_string else map(string.upper, d)


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


_codon_table = {
    'ATG': 'M',
    'TAA': '*', 'TAG': '*', 'TGA': '*', 'TAR': '*', 'TRA': '*',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A', 'GCN': 'A',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R', 'AGA': 'R',
    'AGG': 'R', 'CGN': 'R', 'MGR': 'R',
    'AAT': 'N', 'AAC': 'N', 'AAY': 'N',
    'GAT': 'D', 'GAC': 'D', 'GAY': 'D',
    'TGT': 'C', 'TGC': 'C', 'TGY': 'C',
    'CAA': 'Q', 'CAG': 'Q', 'CAR': 'Q',
    'GAA': 'E', 'GAG': 'E', 'GAR': 'E',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G', 'GGN': 'G',
    'CAT': 'H', 'CAC': 'H', 'CAY': 'H',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATH': 'I',
    'TTA': 'L', 'TTG': 'L', 'CTT': 'L', 'CTC': 'L', 'CTA': 'L',
    'CTG': 'L', 'YTR': 'L', 'CTN': 'L',
    'AAA': 'K', 'AAG': 'K', 'AAR': 'K',
    'TTT': 'F', 'TTC': 'F', 'TTY': 'F',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P', 'CCN': 'P',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S', 'AGT': 'S',
    'AGC': 'S', 'TCN': 'S', 'AGY': 'S',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T', 'ACN': 'T',
    'TGG': 'W',
    'TAT': 'Y', 'TAC': 'Y', 'TAY': 'Y',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V', 'GTN': 'V',
    '': ''
    }


def codon_to_amino_acid(c):
    """
    Given a codon C, return an amino acid or ??? if codon unrecognized.
    Codons could be unrecognized due to ambiguity in IUPAC characters.
    """
    assert len(c) == 3, c
    if c is None:
        return None
    c = c
    if c in _codon_table:
        return _codon_table[c]
    return '?'


def translate_sequence(sequence):
    """
    Translates a given DNA sequence to single-letter amino acid
    space. If the sequence is not a multiple of 3 and is not a unique degenerate codon it will be truncated silently.
    """
    result = []
    sequence = sequence.upper()
    for i in xrange(0, len(sequence) - len(sequence) % 3, 3):
        result.append(codon_to_amino_acid(sequence[i: i + 3]))
    if len(sequence) % 3 == 2:
        c = codon_to_amino_acid(sequence[i + 3:] + "N")
        if c != "?":
            result.append(c)
    return "".join(result)


def read_codons(seq, offset=0, skip_last=True):
    """
    Provides an iterator that reads through a sequence one codon at a time.
    """
    l = len(seq)
    if skip_last:
        l -= 3
    for i in xrange(offset,  l - l % 3, 3):
            yield seq[i:i + 3]


def read_codons_with_position(seq, offset=0, skip_last=True):
    """
    Provides an iterator that reads through a sequence one codon at a time,
    returning both the codon and the start position in the sequence.
    """
    l = len(seq)
    if skip_last:
        l -= 3
    for i in xrange(offset, l - l % 3, 3):
            yield i, seq[i:i + 3]


def get_sequence_dict(file_path, upper=True):
    """
    Returns a dictionary of fasta records. If upper is true, all bases will be uppercased.
    """
    gdx_path = file_path + ".gdx"
    assert os.path.exists(gdx_path), ("Error: gdx does not exist for this fasta. We need the fasta files to be "
                                     "flattened in place prior to running the pipeline because of concurrency issues.")
    if upper is True:
        return Fasta(file_path, record_class=UpperNpyFastaRecord)
    else:
        return Fasta(file_path)
