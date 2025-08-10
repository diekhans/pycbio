# Copyright 2006-2025 Mark Diekhans
import pytest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.hgdata.frame import Frame, FRAME1

def testConstruct():
    # make sure singletons are returned
    f = Frame(1)
    assert f == 1
    assert f is FRAME1

    f = Frame("1")
    assert f == 1
    assert f == Frame(1)
    assert f is FRAME1

def testIncr():
    assert Frame(1).incr(1) == 2
    assert isinstance(Frame(1) + 1, Frame)
    assert isinstance(Frame(1) - 1, Frame)
    assert Frame(1) + 1 == 2
    assert Frame(1) - 1 == 0
    assert Frame(1) + 4 == 2
    assert Frame(1) - 6 == 1
    assert Frame(1) - 7 == 0

def testPhase():
    assert Frame.fromPhase(0) == Frame(0)
    assert Frame.fromPhase(1) == Frame(2)
    assert Frame.fromPhase(2) == Frame(1)
    assert Frame.fromPhase('1') == Frame(2)
    assert Frame.fromPhase('.') is None
    assert Frame.fromPhase(-1) is None
    assert Frame(0).toPhase() == 0
    assert Frame(1).toPhase() == 2
    assert Frame(2).toPhase() == 1

def testFromFrame():
    assert Frame.fromFrame(1) == Frame(1)
    assert Frame.fromFrame("1") == Frame(1)
    assert Frame.fromFrame("-1") is None
    assert Frame.fromFrame(".") is None
    assert Frame.fromFrame(-1) is None

def testErrors():
    with pytest.raises(ValueError) as cm:
        Frame(3)
    assert str(cm.value) == "Frame() argument must be in the range 0..2, got 3"
    with pytest.raises(ValueError) as cm:
        Frame(1.0)
    assert str(cm.value) == "Frame() takes either a Frame, int, or str value as an argument, got <class 'float'>"
