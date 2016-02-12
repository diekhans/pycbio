"""
Test the sequence_lib, psl_lib classes and functions
Original author: Dent Earl
Modified by: Ian Fiddes

"""
from glob import glob
import os
import shutil
import string
import subprocess
import unittest
from pycbio.bio.transcripts import Transcript
from pycbio.bio.bio import get_sequence_dict
from pycbio.bio.psl import PslRow
import random

__author__ = "Ian Fiddes"


def makeTempDirParent():
    """
    make the parent temp dir directory
    """
    if not os.path.exists(os.path.join(os.curdir, '.tempTestDir')):
        os.mkdir(os.path.join(os.curdir, '.tempTestDir'))


def removeTempDirParent():
    """
    remove the parent temp dir directory
    """
    if os.path.exists(os.path.join(os.curdir, '.tempTestDir')):
        shutil.rmtree(os.path.join(os.curdir, '.tempTestDir'))


def makeTempDir(name=None):
    """
    make the directory where all temporary test files will be stored.
    """
    makeTempDirParent()
    charSet = string.ascii_lowercase + '123456789'
    if name is None:
        while True:
            name = '%s_%s' % (''.join(random.choice(charSet) for x in xrange(4)),
                    ''.join(random.choice(charSet) for x in xrange(4)))
            if not os.path.exists(os.path.join(os.curdir, '.tempTestDir', name)):
                break
    if not os.path.exists(os.path.join(os.curdir, '.tempTestDir', name)):
        os.mkdir(os.path.join(os.curdir, '.tempTestDir', name))
    return os.path.join(os.curdir, '.tempTestDir', name)


def removeDir(dirpath):
    """
    destroy a directory
    """
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)
    if glob(os.path.join(os.path.dirname(dirpath), '*')) == []:
        # if this is the last tempDir to be destroyed, destroy the parenself.t.
        removeTempDirParent()


def which(program):
    """
    which() acts like the unix utility which, but is portable between os.
    If the program does not exist in the PATH then 'None' is returned.
    """
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath != '':
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def runCommands(cmds, localTempDir, inPipes=None, outPipes=None, errPipes=None):
    """
    Run commands from CMDS list
    """
    if inPipes is None:
        inPipes = [None] * len(cmds)
    if outPipes is None:
        outPipes = [None] * len(cmds)
    if errPipes is None:
        errPipes = [None] * len(cmds)
    for i, c in enumerate(cmds, 0):
        if inPipes[i] is None:
            sin = None
        else:
            sin = subprocess.PIPE
        if outPipes[i] is None:
            sout = None
        else:
            sout = subprocess.PIPE
        if errPipes[i] is None:
            serr = None
        else:
            serr = subprocess.PIPE
        p = subprocess.Popen(c, cwd=localTempDir, stdin=sin,
                stdout=sout, stderr=serr)
        if inPipes[i] is None:
            sin = None
        else:
            if not os.path.exists(inPipes[i]):
                raise IOError('Unable to locate inPipe file: %s for command %s'
                                            % (inPipes[i], ' '.join(c)))
            sin = open(inPipes[i], 'r').read()
        if outPipes[i] is None:
            pout, perr = p.communicate(sin)
            handleReturnCode(p.returncode, cmds[i])
        else:
            with open(outPipes[i], 'w') as f:
                f.write(p.communicate(sin)[0])
            handleReturnCode(p.returncode, cmds[i])


def handleReturnCode(retcode, cmd):
    """
    handle the return codes from runCommands
    """
    if not isinstance(retcode, int):
        raise TypeError('handleReturnCode takes an integer for '
                'retcode, not a %s.' % retcode.__class__)
    if not isinstance(cmd, list):
        raise TypeError('handleReturnCode takes a list for '
                'cmd, not a %s.' % cmd.__class__)
    if retcode:
        if retcode < 0:
            raise RuntimeError('Experienced an error while trying to execute: '
                    '%s SIGNAL:%d' %(' '.join(cmd), -retcode))
        else:
            raise RuntimeError('Experienced an error while trying to execute: '
                    '%s retcode:%d' %(' '.join(cmd), retcode))


def createSequenceFile(sequences, tmpDir, filename='seq.fa'):
    """
    given a dict (key is (name, comment), value is sequence) return path to temp file.
    """
    seqfile = os.path.join(tmpDir, filename)
    with open(seqfile, 'w') as f:
        for name, sequence in sequences.iteritems():
            f.write(">{}\n{}\n".format(name, sequence))
    subprocess.call("pyfasta flatten {}".format(seqfile), shell=True)
    return seqfile


def createAlignmentFile(alignments, tmpDir):
    """
    given a list of alignments, return path to a temp file.
    """
    alnfile = os.path.join(tmpDir, 'aln.psl')
    with open(alnfile, 'w') as f:
        for a in alignments:
            if isinstance(a, str):
                f.write('%s\n' % a)
            elif isinstance(a, PslRow):
                f.write('%s\n' % a.psl_string())
    return alnfile


def createBedFile(bedLines, name, tmpDir):
    """
    given a list of string bed lines, return path to a temp file.
    """
    bedFile = os.path.join(tmpDir, name)
    with open(bedFile, 'w') as f:
        for b in bedLines:
                f.write('%s\n' % b)
    return bedFile


def bedLine(chrom, chromStart, chromEnd, name, score=None, strand=None,
                    thickStart=None, thickEnd=None, itemRgb=None, blockCount=None,
                    blockSizes=None, blockStarts=None):
    """ Give the fields, create a bed line string
    """

    s = ('%s %d %d %s'
             % (chrom, chromStart, chromEnd, name))
    if score is not None:
        for v in [strand, thickStart, thickEnd, itemRgb,
                blockCount, blockSizes, blockStarts]:
            assert(v is not None)
        s += (' %d %s %d %d %s %d %s %s'
                % (score, strand, thickStart, thickEnd, itemRgb, blockCount,
                blockSizes, blockStarts))
    return s


def simplePsl(strand, qSize, qStart, qEnd, tSize, tStart, tEnd,
                            blockSizes, qStarts, tStarts, qName='query', tName='target'):
    """ Given a few of the fields, create a PslRow object.
    """
    line = ('%d %d %d %d %d %d %d %d %s %s %d %d %d %s %d %d %d %d %s %s %s'
            % (1, 0, 0, 0, 0, 0, 0, 0, strand, qName, qSize, qStart, qEnd,
            tName, tSize, tStart, tEnd, len(blockSizes),
            ','.join([str(b) for b in blockSizes]),
            ','.join([str(b) for b in qStarts]),
            ','.join([str(b) for b in tStarts]),
            ))
    return PslRow(line)


##############################################################################
##############################################################################
#
# The classes below test functions and classes in the sequence_lib library
#
##############################################################################
##############################################################################


class UpperCaseTest(unittest.TestCase):
    def setUp(self):
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1": "GTATTagtcACCTAA"}, tmp)
        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_case(self):
        self.assertEqual(self.chrom_seq["chr1"][:], "GTATTAGTCACCTAA")


class NegativeStrandTranscriptTests(unittest.TestCase):
    """
    Tests the Transcript functionality of sequence_lib.

    Tests the example negative strand BED record drawn out below:


    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T  A  A
    tx       -  -  a  t  T  C  -  T  G  G  -  -  C  t  a  -
    tx.pos         9  8  7  6     5  4  3        2  1  0
    cds.pos              5  4     3  2  1        0

    """

    def setUp(self):
        self.t = Transcript(['chr1', '2', '15', 'A', '0', '-', '4', '13',
                '0,128,0', '3', '4,3,3', '0,5,10'])
        self.transcript_seq = "TAGCCAGAAT"
        self.cds_seq = "GCCAGA"
        self.amino_acid = "AR"
        self.introns = ["GT", "A"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1": "GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_chromosome_invalid_coordinates(self):
        """
        chromosome coordinate translations should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 0, 1, 6, 10, 11, 15, 16, 100):
            self.assertIsNone(self.t.chromosome_coordinate_to_transcript(i))
        for i in (-10, -1, 0, 1, 2, 3, 6, 10, 11, 13, 14, 15, 100):
            self.assertIsNone(self.t.chromosome_coordinate_to_cds(i))

    def test_transcript_invalid_coordinates(self):
        """
        transcript coordinate translation should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 16, 100):
            self.assertIsNone(self.t.transcript_coordinate_to_chromosome(i))
        for i in (-10, -1, 0, 1, 8, 9, 10, 100):
            self.assertIsNone(self.t.transcript_coordinate_to_cds(i))

    def test_cds_invalid_coordinates(self):
        """
        CDS coordinate translations should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 6, 100):
            self.assertIsNone(self.t.cds_coordinate_to_chromosome(i))
            self.assertIsNone(self.t.cds_coordinate_to_transcript(i))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [None, None, None, None, 5, 4, None, 3, 2, 1, None, None, 0, None, None, None]
        transcript_result = [None, None, 9, 8, 7, 6, None, 5, 4, 3, None, None, 2, 1, 0, None]
        for i in xrange(16):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [14, 13, 12, 9, 8, 7, 5, 4, 3, 2, None]
        cds_result = [None, None, 0, 1, 2, 3, 4, 5, None, None, None]
        for i in xrange(11):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [12, 9, 8, 7, 5, 4]
        transcript_result = [2, 3, 4, 5, 6, 7]
        for i in xrange(6):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(16):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)

    def test_amino_acid_slicing(self):
        """
        Tests the conversion of chromosome/transcript/cds coordinates into
        individual amino acids.
        """
        chrom_result = [None, None, None, None, "R", "R", None, "R", "A", "A", None, None,
                "A", None, None, None]
        for i in xrange(len(chrom_result)):
            self.assertEqual(self.t.chromosome_coordinate_to_amino_acid(i, self.chrom_seq), chrom_result[i])
        cds_result = ["A", "A", "A", "R", "R", "R", None]
        for i in xrange(len(cds_result)):
            self.assertEqual(self.t.cds_coordinate_to_amino_acid(i, self.chrom_seq), cds_result[i])
        transcript_result = [None, None, "A", "A", "A", "R", "R", "R", None, None, None]
        for i in xrange(len(transcript_result)):
            self.assertEqual(self.t.transcript_coordinate_to_amino_acid(i, self.chrom_seq), transcript_result[i])


class PositiveStrandTranscriptTests(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example positive strand BED record drawn out below:

    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T  A  A
    tx       -  -  a  t  T  C  -  T  G  G  -  -  C  t  a  -
    tx.pos         0  1  2  3     4  5  6        7  8  9
    cds.pos              0  1     2  3  4        5

    """

    def setUp(self):
        self.t = Transcript(['chr1', '2', '15', 'A', '0', '+', '4', '13',
                '0,128,0', '3', '4,3,3', '0,5,10'])
        self.transcript_seq = "ATTCTGGCTA"
        self.cds_seq = "TCTGGC"
        self.amino_acid = "SG"
        self.introns = ["T", "AC"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_chromosome_invalid_coordinates(self):
        """
        chromosome coordinate translations should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 0, 1, 6, 10, 11, 16, 100):
            self.assertIsNone(self.t.chromosome_coordinate_to_transcript(i))
        for i in (-10, -1, 0, 1, 2, 3, 6, 10, 11, 15, 100):
            self.assertIsNone(self.t.chromosome_coordinate_to_cds(i))

    def test_transcript_invalid_coordinates(self):
        """
        transcript coordinate translation should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 16, 100):
            self.assertIsNone(self.t.transcript_coordinate_to_chromosome(i))
        for i in (-10, -1, 0, 1, 9, 10, 100):
            self.assertIsNone(self.t.transcript_coordinate_to_cds(i))

    def test_cds_invalid_coordinates(self):
        """
        CDS coordinate translations should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 6, 100):
            self.assertIsNone(self.t.cds_coordinate_to_chromosome(i))
            self.assertIsNone(self.t.cds_coordinate_to_transcript(i))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [None, None, None, None, 0, 1, None, 2, 3, 4, None, None, 5, None, None, None]
        transcript_result = [None, None, 0, 1, 2, 3, None, 4, 5, 6, None, None, 7, 8, 9, None]
        for i in xrange(16):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [2, 3, 4, 5, 7, 8, 9, 12, 13, 14, None]
        cds_result = [None, None, 0, 1, 2, 3, 4, 5, None, None, None]
        for i in xrange(11):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [4, 5, 7, 8, 9, 12]
        transcript_result = [2, 3, 4, 5, 6, 7]
        for i in xrange(6):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(16):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)

    def test_amino_acid_slicing(self):
        """
        Tests the conversion of chromosome/transcript/cds coordinates into
        individual amino acids.
        """
        chrom_result = [None, None, None, None, "S", "S", None, "S", "G", "G", None, None,
                "G", None, None, None]
        for i in xrange(len(chrom_result)):
            self.assertEqual(self.t.chromosome_coordinate_to_amino_acid(i, self.chrom_seq), chrom_result[i])
        cds_result = ["S", "S", "S", "G", "G", "G", None]
        for i in xrange(len(cds_result)):
            self.assertEqual(self.t.cds_coordinate_to_amino_acid(i, self.chrom_seq), cds_result[i])
        transcript_result = [None, None, "S", "S", "S", "G", "G", "G", None, None, None]
        for i in xrange(len(transcript_result)):
            self.assertEqual(self.t.transcript_coordinate_to_amino_acid(i, self.chrom_seq), transcript_result[i])


class SingleExonTranscript1(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example single exon transcript below:

    chrom    0  1  2  3  4  5
    seq      G  T  A  T  T  C
    tx       g  T  A  T  t  c
    tx.pos   0  1  2  3  4  5
    cds.pos     0  1  2

    """

    def setUp(self):
        self.t = Transcript(['chr1', '0', '6', 'A', '0', '+', '1', '4', '0,128,0', '1', '6', '0'])
        self.transcript_seq = "GTATTC"
        self.cds_seq = "TAT"
        self.amino_acid = "Y"
        self.introns = []
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_transcript_invalid_coordinates(self):
        """
        transcript coordinate translation should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 6, 100):
            self.assertIsNone(self.t.transcript_coordinate_to_chromosome(i))
        for i in (-10, -1, 0, 4, 5, 9, 10, 100):
            self.assertIsNone(self.t.transcript_coordinate_to_cds(i))

    def test_cds_invalid_coordinates(self):
        """
        CDS coordinate translations should return None if the coordinate is invalid
        in other spaces
        """
        for i in (-10, -1, 4, 100):
            self.assertIsNone(self.t.cds_coordinate_to_chromosome(i))
            self.assertIsNone(self.t.cds_coordinate_to_transcript(i))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [None, 0, 1, 2, None, None, None]
        transcript_result = [0, 1, 2, 3, 4, 5, None]
        for i in xrange(6):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [0, 1, 2, 3, 4, 5, None]
        cds_result = [None, 0, 1, 2, None, None, None]
        for i in xrange(6):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [1, 2, 3, None]
        transcript_result = [1, 2, 3, None]
        for i in xrange(4):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 7):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)

    def test_amino_acid_slicing(self):
        """
        Tests the conversion of chromosome/transcript/cds coordinates into
        individual amino acids.
        """
        chrom_result = [None, "Y", "Y", "Y", None, None, None]
        for i in xrange(len(chrom_result)):
            self.assertEqual(self.t.chromosome_coordinate_to_amino_acid(i, self.chrom_seq), chrom_result[i])
        cds_result = ["Y", "Y", "Y", None]
        for i in xrange(len(cds_result)):
            self.assertEqual(self.t.cds_coordinate_to_amino_acid(i, self.chrom_seq), cds_result[i])
        transcript_result = [None, "Y", "Y", "Y", None, None, None, None]
        for i in xrange(len(transcript_result)):
            self.assertEqual(self.t.transcript_coordinate_to_amino_acid(i, self.chrom_seq), transcript_result[i])


class SingleExonTranscript2(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example single exon transcript below:

    chrom    0  1  2  3  4  5
    seq      G  T  A  T  T  C
    tx       G  T  A  T  T  C
    tx.pos   0  1  2  3  4  5
    cds.pos  0  1  2  3  4  5

    """

    def setUp(self):
        self.t = Transcript(['chr1', '0', '6', 'A', '0', '+', '0', '6', '0,128,0', '1', '6', '0'])
        self.transcript_seq = "GTATTC"
        self.cds_seq = self.transcript_seq
        self.amino_acid = "VF"
        self.introns = []
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = transcript_result = [0, 1, 2, 3, 4, 5, None]
        for i in xrange(6):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = cds_result = [0, 1, 2, 3, 4, 5, None]
        for i in xrange(6):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = transcript_result = [0, 1, 2, 3, 4, 5, None]
        for i in xrange(6):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 7):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class SingleExonTranscript3(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example single exon transcript below:

    chrom    0  1  2  3  4  5
    seq      G  T  A  T  T  C
    tx       G  T  A  T  T  c
    tx.pos   5  4  3  2  1  0
    cds.pos  4  3  2  1  0

    """

    def setUp(self):
        self.t = Transcript(['chr1', '0', '6', 'A', '0', '-', '0', '5', '0,128,0', '1', '6', '0'])
        self.transcript_seq = "GAATAC"
        self.cds_seq = "AATAC"
        self.amino_acid = "NT"  # ACN is unambiguously Threonine 
        self.introns = []
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [4, 3, 2, 1, 0, None, None]
        transcript_result = [5, 4, 3, 2, 1, 0, None]
        for i in xrange(7):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [5, 4, 3, 2, 1, 0, None, None]
        cds_result = [None, 0, 1, 2, 3, 4, None]
        for i in xrange(7):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [4, 3, 2, 1, 0, None]
        transcript_result = [1, 2, 3, 4, 5, None]
        for i in xrange(6):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 7):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class SingleExonTranscript4(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example single exon transcript below:

    chrom    0  1  2  3  4  5  6  7  8  9  10
    seq      G  T  A  T  T  C  T  T  G  G  A
    tx       G  T  A  T  T  C  t  t  g  g  a
    tx.pos   10 9  8  7  6  5  4  3  2  1  0
    cds.pos  5  4  3  2  1  0

    """

    def setUp(self):
        self.t = Transcript(['chr1', '0', '11', 'A', '0', '-', '0', '6', '0,128,0', '1', '11', '0'])
        self.transcript_seq = "TCCAAGAATAC"
        self.cds_seq = "GAATAC"
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [5, 4, 3, 2, 1, 0]
        transcript_result = [5, 6, 7, 8, 9, 10]
        for i in xrange(6):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])


class NoncodingTranscript(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example non-coding spliced transcript below:

    chrom    0  1  2  3  4  5  6  7  8  9  10
    seq      G  T  A  T  T  C  T  T  G  G  A
    tx       g  t  a  t  -  -  t  -  g  g  a
    tx.pos   0  1  2  3        4     5  6  7

    """

    def setUp(self):
        self.t = Transcript(['chr1', '0', '11', 'A', '0', '+', '0', '0', '0,128,0', '3', '4,1,3', '0,6,8'])
        self.transcript_seq = "GTATTGGA"
        self.cds_seq = ""
        self.amino_acid = ""
        self.introns = ["TC", "T"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [None] * 12
        transcript_result = [0, 1, 2, 3, None, None, 4, None, 5, 6, 7, None]
        for i in xrange(12):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [0, 1, 2, 3, 6, 8, 9, 10, None]
        cds_result = [None] * 9
        for i in xrange(9):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = transcript_result = [None] * 10
        for i in xrange(10):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 12):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class ComplicatedTranscript1(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example complicated transcript below:

    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T  A  A  G  C  C  T  G
    tx       -  t  a  t  -  -  t  t  G  G  -  -  -  T  A  A  -  c  c  t  -
    tx.pos      0  1  2        3  4  5  6           7  8  9     10 11 12
    cds.pos                          0  1           2  3  4

    """

    def setUp(self):
        self.t = Transcript(['chr1', '1', '20', 'A', '0', '+', '8', '16', '0,128,0', '4', '3,4,3,3', '0,5,12,16'])
        self.transcript_seq = "TATTTGGTAACCT"
        self.cds_seq = "GGTAA"
        self.amino_acid = "G"
        self.introns = ["TC", "ACC", "G"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAAGCCTG"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [None, None, None, None, None, None, None, None, 0, 1, None, None, None, 2, 3, 4, None, None, None, None, None]
        transcript_result = [None, 0, 1, 2, None, None, 3, 4, 5, 6, None, None, None, 7, 8, 9, None, 10, 11, 12, None]
        for i in xrange(21):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [1, 2, 3, 6, 7, 8, 9, 13, 14, 15, 17, 18, 19]
        cds_result = [None, None, None, None, None, 0, 1, 2, 3, 4, None, None, None]
        for i in xrange(13):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [8, 9, 13, 14, 15]
        transcript_result = [5, 6, 7, 8, 9]
        for i in xrange(5):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 12):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class ComplicatedTranscript2(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example negative strand complicated transcript below:

    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T  A  A  G  C  C  T  G
    tx       -  t  a  t  -  -  t  T  G  G  -  -  -  T  A  A  -  c  c  t  -
    tx.pos      12 11 10       9  8  7  6           5  4  3     2  1  0
    cds.pos                       5  4  3           2  1  0

    """

    def setUp(self):
        self.t = Transcript(['chr1', '1', '20', 'A', '0', '-', '7', '16', '0,128,0', '4', '3,4,3,3', '0,5,12,16'])
        self.transcript_seq = "AGGTTACCAAATA"
        self.cds_seq = "TTACCA"
        self.amino_acid = "LP"
        self.introns = ["C", "GGT", "GA"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAAGCCTG"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sizes(self):
        """
        Make sure sizes are correct
        """
        self.assertEqual(len(self.t), len(self.transcript_seq))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), len(self.cds_seq))
        self.assertEqual(len(self.t.get_protein_sequence(self.chrom_seq)), len(self.amino_acid))
        self.assertEqual(len(self.t.get_cds(self.chrom_seq)), self.t.cds_size)

    def test_chromosome_coordinate_translations(self):
        """
        Check all possible chromosome translations for correct result
        """
        cds_result = [None, None, None, None, None, None, None, 5, 4, 3, None, None, None, 2, 1, 0, None, None, None, None, None]
        transcript_result = [None, 12, 11, 10, None, None, 9, 8, 7, 6, None, None, None, 5, 4, 3, None, 2, 1, 0, None]
        for i in xrange(21):
            self.assertEqual(self.t.chromosome_coordinate_to_cds(i), cds_result[i])
            self.assertEqual(self.t.chromosome_coordinate_to_transcript(i), transcript_result[i])

    def test_transcript_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [19, 18, 17, 15, 14, 13, 9, 8, 7, 6, 3, 2, 1]
        cds_result = [None, None, None, 0, 1, 2, 3, 4, 5, None, None, None, None]
        for i in xrange(13):
            self.assertEqual(self.t.transcript_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.transcript_coordinate_to_cds(i), cds_result[i])

    def test_cds_coordinate_translations(self):
        """
        Check all possible transcript translations for correct result
        """
        chrom_result = [15, 14, 13, 9, 8, 7]
        transcript_result = [3, 4, 5, 6, 7, 8]
        for i in xrange(5):
            self.assertEqual(self.t.cds_coordinate_to_chromosome(i), chrom_result[i])
            self.assertEqual(self.t.cds_coordinate_to_transcript(i), transcript_result[i])

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 12):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class PositiveStrandGenePredTranscript(PositiveStrandTranscriptTests):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example positive strand BED record drawn out below:

    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T  A  A
    tx       -  -  a  t  T  C  -  T  G  G  -  -  C  t  a  -
    tx.pos         0  1  2  3     4  5  6        7  8  9
    cds.pos              0  1     2  3  4        5

    """

    def setUp(self):
        self.t = GenePredTranscript(['A', 'chr1', '+', '2', '15', '4', '13', '3', '2,7,12', '6,10,15', '1',
                                             'q2', 'cmpl', 'cmpl', '2,0,0'])
        self.transcript_seq = "ATTCTGGCTA"
        self.cds_seq = "TCTGGC"
        self.amino_acid = "LA"  # this transcript has a offset of 2, so the first in-frame codon is TGG
        self.introns = ["T", "AC"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class NegativeStrandGenePredTranscript(NegativeStrandTranscriptTests):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example positive strand BED record drawn out below:

    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T  A  A
    tx       -  -  a  t  T  C  -  T  G  G  -  -  C  t  a  -
    tx.pos         0  1  2  3     4  5  6        7  8  9
    cds.pos              0  1     2  3  4        5

    """

    def setUp(self):
        self.t = GenePredTranscript(['A', 'chr1', '-', '2', '15', '4', '13', '3', '2,7,12', '6,10,15', '1',
                                             'q2', 'cmpl', 'cmpl', '0,0,1'])
        self.transcript_seq = "TAGCCAGAAT"
        self.cds_seq = "GCCAGA"
        self.amino_acid = "Q"  # this transcript has a offset of 1, so the first in-frame codon is CAG
        self.introns = ["GT", "A"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAA"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)


class ZeroBasepairIntron(unittest.TestCase):
    """
    Tests the Transcript functionality part of sequence_lib.

    Tests the example transcript below which contains a 0bp 'intron' due to a deletion

    chrom    0  1  2  3  4  5  6  7  8  9  10 11 12 13
    seq      G  T  A  T  T  C  T  T  G  G  A  C  C  T
    tx       -  t  a  t  t  c  t  T  G  G  -  -  -  T
    tx.pos      0  1  2  3  4  5  6  7  8  -  -  -  9
    cds.pos                  ^^   0  1  2           3

    """

    def setUp(self):
        self.t = Transcript(['chr1', '1', '14', 'A', '0', '+', '7', '14', '0,128,0', '3', '5,4,1', '0,5,12'])
        self.transcript_seq = "TATTCTTGGT"
        self.cds_seq = "TGGT"
        self.amino_acid = "W"
        self.introns = ["", "ACC"]
        tmp = os.path.abspath(makeTempDir())
        createSequenceFile({"chr1":"GTATTCTTGGACCTAAGCCTG"}, tmp)

        self.chrom_seq = get_sequence_dict(os.path.join(tmp, "seq.fa"))
        self.addCleanup(removeDir, tmp)

    def test_sequences(self):
        """
        Tests that the proper sequences are created from the intervals
        """
        self.assertEqual(self.t.get_mrna(self.chrom_seq), self.transcript_seq)
        self.assertEqual(self.t.get_cds(self.chrom_seq), self.cds_seq)
        self.assertEqual(self.t.get_protein_sequence(self.chrom_seq), self.amino_acid)
        self.assertEqual(self.t.get_intron_sequences(self.chrom_seq), self.introns)

    def test_reciprocal_translations(self):
        """
        Test reciprocal translations between coordinate spaces
        """
        for i in xrange(-1, 12):
            tmp = self.t.chromosome_coordinate_to_transcript(i)
            #can't have reciprocal connection once None appears
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_chromosome(tmp), i)

            tmp = self.t.chromosome_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.transcript_coordinate_to_chromosome(i)
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)

            tmp = self.t.transcript_coordinate_to_cds(i)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_transcript(tmp), i)

            tmp = self.t.cds_coordinate_to_transcript(i)
            if tmp is not None:
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.chromosome_coordinate_to_transcript(i)
            if tmp is not None:
                tmp = self.t.transcript_coordinate_to_cds(tmp)
            if tmp is not None:
                self.assertEqual(self.t.cds_coordinate_to_chromosome(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(i)
            if tmp is not None:
                tmp = self.t.chromosome_coordinate_to_transcript(tmp)
                self.assertEqual(self.t.transcript_coordinate_to_cds(tmp), i)

            tmp = self.t.cds_coordinate_to_chromosome(self.t.transcript_coordinate_to_cds(i))
            if tmp is not None:
                self.assertEqual(self.t.chromosome_coordinate_to_transcript(tmp), i)


if __name__ == '__main__':
    unittest.main()