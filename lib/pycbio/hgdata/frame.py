# Copyright 2006-2012 Mark Diekhans
from pycbio.sys import PycbioException


class Frame(int):
    """Immutable object the represents a frame, integer value of 0, 1, or 2.
    This is also an int.  Use None if there is no frame."""

    __slots__ = ()

    @staticmethod
    def _checkFrameValue(val):
        if not ((val >= 0) and (val <= 2)):
            raise TypeError("frame must be an integer in the range 0..2, got {}".format(val))

    def __new__(cls, val):
        obj = super(Frame, cls).__new__(cls, val)
        cls._checkFrameValue(obj)
        return obj

    @staticmethod
    def fromPhase(phase):
        """construct a Frame from a GFF/GTF like phase, which maybe an int or str"""
        if isinstance(phase, str):
            phase = int(phase)
        if phase == 0:
            return Frame(0)
        elif phase == 1:
            return Frame(2)
        elif phase == 2:
            return Frame(1)
        else:
            raise PycbioException("invalid phase: {}".format(phase))

    def toPhase(self):
        """frame expressed as a GFF/GTF like phase, which is the number of bases
        to the start of the next codon"""
        if self == 0:
            return 0
        elif self == 1:
            return 2
        else:
            return 1

    def incr(self, amt):
        """increment frame by positive or negative amount, returning a new
            Frame object.  Frame of -1 already returns -1."""
        if not isinstance(amt, int):
            raise ValueError("can only increment a frame by an int value: {} {}".format(type(amt), amt))
        val = int(self)  # prevent infinite recursion
        if amt >= 0:
            return Frame((val + amt) % 3)
        else:
            amt3 = (-amt) % 3
            return Frame((val - (amt - amt3)) % 3)

    def __add__(self, amt):
        return self.incr(amt)

    def __sub__(self, amt):
        return self.incr(-amt)
