# Copyright 2006-2025 Mark Diekhans
import pytest
import sys
import pickle

if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.hgdata.coords import Coords, CoordsError, reverseRange, reverseStrand
def testCoordsParse():
    def check(c):
        assert c.name == "chr22"
        assert c.start == 10000
        assert c.end == 20000

    check(Coords.parse("chr22:10000-20000"))
    check(Coords.parse("chr22:10,000-20,000"))
    check(Coords.parse("chr22:10,001-20,000", oneBased=True))

def testCoordsParseFullSeq():
    c = Coords.parse("chr22")
    assert c.name == "chr22"
    assert c.start is None
    assert c.end is None

    c = Coords.parse("chr22", size=50818468)
    assert c.name == "chr22"
    assert c.start == 0
    assert c.end == 50818468

def testCoordsSimple():
    c = Coords("chr22", 10000, 20000)
    assert c.name == "chr22"
    assert c.start == 10000
    assert c.end == 20000

def testCoordsParseExtra():
    c = Coords.parse("chr22:10000-20000", strand='-', size=50818468)
    assert c.name == "chr22"
    assert c.start == 10000
    assert c.end == 20000
    assert c.strand == '-'
    assert c.size == 50818468

def testReverse():
    c = Coords("chr22", 10000, 20000, strand='-', size=50818468)
    cr = Coords("chr22", 50798468, 50808468, strand='+', size=50818468)
    assert c.reverse() == cr
    assert c == cr.reverse()
    c = Coords("chr22", 10000, 20000, size=50818468)
    cr = Coords("chr22", 50798468, 50808468, size=50818468)

def testAbs():
    c = Coords("chr22", 50798468, 50808468, strand='-', size=50818468)
    ca = Coords("chr22", 10000, 20000, strand='+', size=50818468)
    assert c.abs() == ca
    assert c != ca.abs()

def testAdjust():
    c = Coords("chr22", 50798468, 50808468, strand='-', size=50818468)
    ca = c.adjust(start=50798486, strand=None)
    assert ca == Coords("chr22", 50798486, 50808468, strand=None, size=50818468)

def testOverlaps():
    # strand-specific
    c1 = Coords("chr22", 40000000, 50000000, strand='-', size=50818468)
    c2 = Coords("chr22", 35000000, 45000000, strand='-', size=50818468)
    assert c1.overlaps(c2)
    assert c2.overlaps(c1)
    assert c1.reverse().overlaps(c2.reverse())
    assert c1.abs().overlaps(c1.abs())

    # reversing, overlap with different strand
    assert c1.overlaps(c2.reverse())
    assert c1.reverse().overlaps(c2)

    # overlap coords, different strand
    c3 = Coords("chr22", 35000000, 45000000, strand='+', size=50818468)
    assert not c1.overlaps(c3)

    # overlap with None strand, treated as positive
    cp = Coords("chr22", 40000000, 45000000, strand='+', size=50818468)
    cn = Coords("chr22", 35000000, 45000000, strand=None, size=50818468)
    assert cn.overlaps(cp)

    # same-strand comparison without sizes works
    c5 = Coords("chr22", 40000000, 50000000, strand='-')
    c6 = Coords("chr22", 35000000, 45000000, strand='-')
    assert c5, c6

    # different-strand comparison without sizes is an error
    c7 = Coords("chr22", 35000000, 45000000, strand='-')
    with pytest.raises(ValueError) as cm:
        c3.overlaps(c7)
    assert str(cm.value) == "overlap comparison when different strands and without size: Coords(name='chr22', start=35000000, end=45000000, strand='+', size=50818468).overlaps(Coords(name='chr22', start=35000000, end=45000000, strand='-', size=None)"

def testIntersect():
    # strand-specific
    c1 = Coords("chr22", 40000000, 50000000, strand='-', size=50818468)
    c2 = Coords("chr22", 35000000, 45000000, strand='-', size=50818468)
    ci = c1.intersect(c2)
    assert ci == Coords("chr22", 40000000, 45000000, strand='-', size=50818468)
    c1p = c1.adjust(strand='+')
    c2p = c2.adjust(strand='+')
    cip = c1p.intersect(c2p)
    assert cip == Coords("chr22", 40000000, 45000000, strand='+', size=50818468)
    # defaulted strand
    c2d = c2.adjust(strand=None)
    cid = c1p.intersect(c2d)
    assert cid == Coords("chr22", 40000000, 45000000, strand='+', size=50818468)

def testContains():
    c1 = Coords("chr22", 40000000, 50000000)
    assert not c1.contains(Coords("chr22", 35000000, 45000000))
    assert not c1.contains(Coords("chr22", 35000000, 36000000))
    assert c1.contains(Coords("chr22", 40000000, 50000000))
    assert c1.contains(Coords("chr22", 45000000, 49000000))

def testSubrangeNoStrand():
    c1 = Coords("chr22", 40000000, 50000000, strand='+', size=50818468)
    c2 = c1.subrange(41000000, 49000000)
    assert c2 == Coords("chr22", 41000000, 49000000, strand='+', size=50818468)

def testSubrangeStrandSwap():
    c1 = Coords("chr22", 40000000, 50000000, strand='+', size=50818468)
    c2 = c1.subrange(1818468, 9818468, strand='-')
    assert c2 == Coords("chr22", 41000000, 49000000, strand='+', size=50818468)

def testAdjrange():
    c1 = Coords("chr22", 400000, 500000, strand='+', size=50818468)
    c2 = c1.adjrange(41000000, 49000000)
    assert c2 == Coords("chr22", 41000000, 49000000, strand='+', size=50818468)

def testAdjrangeStart():
    c1 = Coords("chr22", 400000, 500000, strand='+', size=50818468)
    c2 = c1.adjrange(1000, None)
    assert c2 == Coords("chr22", 1000, 500000, strand='+', size=50818468)

def testAdjrangeEnd():
    c1 = Coords("chr22", 400000, 500000, strand='+', size=50818468)
    c2 = c1.adjrange(None, 49000000)
    assert c2 == Coords("chr22", 400000, 49000000, strand='+', size=50818468)

def testCoordsGetAbs():
    cpos = Coords("chr22", 40000000, 45000000, strand='+', size=50818468)
    cneg = cpos.reverse()
    assert (cneg.absStart, cneg.absEnd) == (cpos.start, cpos.end)

def testFormat():
    pos = Coords("chr22", 40000000, 45000000, strand='+', size=50818468)
    assert pos.format() == "chr22:40000000-45000000"
    assert pos.format(oneBased=True) == "chr22:40000001-45000000"
    assert pos.format(commas=True) == "chr22:40,000,000-45,000,000"
    assert pos.format(oneBased=True, commas=True) == "chr22:40,000,001-45,000,000"

def test_pickle():
    c1 = Coords("chr22", 40000000, 50000000, strand='+', size=50818468)
    c2 = pickle.loads(pickle.dumps(c1))
    assert c2 == c1

def FIXME_testCoordsCmpNoStrand():
    # strand None comparison must be handled carefully, can't do None < None
    cs = [Coords("chr22", 10200, 20000),
          Coords("chr1", 90200, 990000),
          Coords("chr22", 10000, 20000),
          Coords("chr22", 10000, 10000)]

    assert sorted(cs, key=lambda c: (c.name, c.start, c.end)) == sorted(cs)

def FIXME_testCoordsCmpStrand():
    cs = [Coords("chr22", 10200, 20000, '-'),
          Coords("chr1", 90200, 990000, '+'),
          Coords("chr22", 10400, 20000, '-'),
          Coords("chr22", 10200, 20000, '+'),
          Coords("chr22", 10000, 10000, '-')]
    assert sorted(cs, key=lambda c: (c.name, c.start, c.end, c.strand)) == sorted(cs)

def FIXME_testCoordsSortRegress():
    # regression from real data
    cs = [Coords(name='chrY', start=57183100, end=57197337),
          Coords(name='chrY', start=22439592, end=22442458),
          Coords(name='chrY', start=22143965, end=22146831),
          Coords(name='chrY', start=9753155, end=9775289),
          Coords(name='chrY', start=6389430, end=6411564),
          Coords(name='chrX', start=155996580, end=156010817),
          Coords(name='chrX', start=65269912, end=65273019),
          Coords(name='chr22', start=29436533, end=29479868),
          Coords(name='chr19', start=54531691, end=54545771),
          Coords(name='chr17', start=15674475, end=15675643),
          Coords(name='chr16', start=90004870, end=90020890),
          Coords(name='chr14', start=61569404, end=61658696),
          Coords(name='chr12', start=68472740, end=68474902),
          Coords(name='chr12', start=30978307, end=31007010),
          Coords(name='chr12', start=8940360, end=8950761),
          Coords(name='chr12', start=2793969, end=2805423),
          Coords(name='chr11', start=64304496, end=64316743),
          Coords(name='chr11', start=61746492, end=61758655),
          Coords(name='chr10', start=119620067, end=119621880),
          Coords(name='chr7', start=127587385, end=127591700),
          Coords(name='chr7', start=100569130, end=100571136),
          Coords(name='chr7', start=26533120, end=26539788),
          Coords(name='chr6', start=143494811, end=143512720),
          Coords(name='chr4', start=139698143, end=139699554),
          Coords(name='chr4', start=11393149, end=11430564),
          Coords(name='chr3', start=50154044, end=50189075),
          Coords(name='chr2', start=237048598, end=237057167),
          Coords(name='chr2', start=72129237, end=72148862),
          Coords(name='chr2', start=37230630, end=37253403),
          Coords(name='chr1', start=171136739, end=171161568),
          Coords(name='chr1', start=67521298, end=67532612),
          Coords(name='chr1', start=1698941, end=1701782),
          Coords(name='chr1', start=922922, end=944575),
          Coords(name='chr5', start=270669, end=438291)]
    assert sorted(cs, key=lambda c: (c.name, c.start, c.end, c.strand)) == sorted(cs)

###
# Helper function tests
###
def testReverseRange():
    """Test reverseRange function"""
    start, end = reverseRange(100, 200, 1000)
    assert start == 800
    assert end == 900
    # Should raise ValueError if size is None
    with pytest.raises(ValueError):
        reverseRange(100, 200, None)

def testReverseStrand():
    """Test reverseStrand function"""
    assert reverseStrand('+') == '-'
    assert reverseStrand('-') == '+'
    assert reverseStrand(None) is None

###
# Coords error handling tests
###
def testCoordsErrorInvalidStart():
    """Test that invalid start raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", "invalid", 1000)

def testCoordsErrorInvalidEnd():
    """Test that mismatched start/end raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", 100, None)

def testCoordsErrorInvalidRange():
    """Test that start > end raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", 1000, 100)

def testCoordsErrorNegativeStart():
    """Test that negative start raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", -100, 100)

def testCoordsErrorExceedsSize():
    """Test that end > size raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", 100, 1000, size=500)

def testCoordsErrorInvalidStrand():
    """Test that invalid strand raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", 100, 200, strand='X')

def testCoordsErrorInvalidSize():
    """Test that invalid size raises CoordsError"""
    with pytest.raises(CoordsError):
        Coords("chr22", 100, 200, size="invalid")

###
# Coords method tests
###
def testCoordsLen():
    """Test Coords.__len__"""
    c = Coords("chr22", 100, 200)
    assert len(c) == 100

def testCoordsStr():
    """Test Coords.__str__"""
    c = Coords("chr22", 100, 200)
    assert str(c) == "chr22:100-200"
    c2 = Coords("chr22", None, None)
    assert str(c2) == "chr22"

def testCoordsHash():
    """Test Coords.__hash__"""
    c1 = Coords("chr22", 100, 200, '+', 50818468)
    c2 = Coords("chr22", 100, 200, '+', 50818468)
    assert hash(c1) == hash(c2)
    # Can be used in sets
    s = {c1, c2}
    assert len(s) == 1

def testCoordsBase():
    """Test Coords.base method"""
    c = Coords("chr22", 100, 200, '+', 50818468)
    cb = c.base()
    assert cb.name == "chr22"
    assert cb.start == 100
    assert cb.end == 200
    assert cb.strand is None
    assert cb.size is None
    # If already base, returns same
    cb2 = cb.base()
    assert cb2 is cb

def testCoordsOverlapsStrand():
    """Test Coords.overlapsStrand method"""
    c1 = Coords("chr22", 100, 200, '+')
    c2 = Coords("chr22", 150, 250, '+')
    c3 = Coords("chr22", 150, 250, '-')
    assert c1.overlapsStrand(c2)
    assert not c1.overlapsStrand(c3)

def testCoordsEqLoc():
    """Test Coords.eqLoc method"""
    c1 = Coords("chr22", 100, 200, '+', 50818468)
    c2 = Coords("chr22", 100, 200, '+', 1000)  # different size
    c3 = Coords("chr22", 100, 200, '-', 50818468)  # different strand
    assert c1.eqLoc(c2)  # size doesn't matter
    assert not c1.eqLoc(c3)  # strand matters

def testCoordsEqAbsLoc():
    """Test Coords.eqAbsLoc method"""
    c1 = Coords("chr22", 100, 200, '+', 1000)
    c2 = Coords("chr22", 800, 900, '-', 1000)  # reverse of c1
    assert c1.eqAbsLoc(c2)
    # Same strand, same coords
    c3 = Coords("chr22", 100, 200, '+', 1000)
    assert c1.eqAbsLoc(c3)

def testCoordsParseInvalidStrand():
    """Test parse with invalid strand"""
    with pytest.raises(CoordsError):
        Coords.parse("chr22:100-200", strand='X')
