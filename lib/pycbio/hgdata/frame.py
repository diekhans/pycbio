# Copyright 2006-2012 Mark Diekhans

# FIXME: should None just be uses a no frame?

class Frame(int):
    """Immutable object the represents a frame, integer value of 0, 1, 2, or
    -1 for no frame.  This is also an int"""

    __slots__ = ()

    @staticmethod
    def __checkFrameValue(val):
        if not ((val >= -1) and (val <= 2)):
            raise TypeError("frame must be an integer in the range -1..2, got {}".format(val))
    
    def __new__(cls, val=-1):
        obj = super(Frame, cls).__new__(cls, val)
        cls.__checkFrameValue(obj)
        return obj

    @staticmethod
    def fromPhase(phase):
        """construct a Frame from a GFF/GTF like phase"""
        if isinstance(phase, str):
            phase = int(phase)
        if phase < 0:
            return Frame(-1)
        elif phase == 0:
            return Frame(0)
        elif phase == 1:
            return Frame(2)
        elif phase == 2:
            return Frame(1)
        else:
            raise Exception("invalid phase: " + str(phase))

    def toPhase(self):
        """frame expressed as a GFF/GTF like phase, which is the number of bases
        to the start of the next codon"""
        if frame == 0:
            return 0
        elif frame == 1:
            return 2
        elif frame == 2:
            return 1
        else:
            return -1

    def incr(self, amt):
        """increment frame by positive or negative amount, returning a new
            Frame object.  Frame of -1 already returns -1."""
        val = int(self)
        if val < 0:
            return self  # no frame, not changed
        elif val >= 0:
            return Frame((val + amt) % 3)
        else:
            amt3 = (-amt) % 3
            return Frame((val - (amt - amt3)) % 3)

    def __add__(self, amt):
        if not isinstance(amt, int):
            return NotImplemented
        return self.incr(amt)

    def __sub__(self, amt):
        if not isinstance(amt, int):
            return NotImplemented
        return self.incr(-amt)
