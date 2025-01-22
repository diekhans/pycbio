# Copyright 2006-2025 Mark Diekhans
from pycbio import PycbioException

# singleton instances for each supported value, initialized after class is created
FRAME0 = None
FRAME1 = None
FRAME2 = None
_frames = None

class Frame(int):
    """Immutable object the represents a frame, integer value of 0, 1, or 2.
    This object is also an int.  Use None if there is no frame, not a Frame instance.
    Frames implement a set of singletons to minimize memory usage.

    val - an int, str convertible to an int, or another Frame.
    """
    __slots__ = ()

    @staticmethod
    def _checkFrameValue(val):
        if not ((val >= 0) and (val <= 2)):
            raise TypeError("frame must be an integer in the range 0..2, got {}".format(val))

    def __new__(cls, val):
        if not (isinstance(val, (Frame, int, str))):
            raise ValueError(f"Frame() takes either a Frame, int, or str value as an argument, got {type(val)}")
        if isinstance(val, str):
            val = int(val)
        if not (0 <= val <= 2):
            raise ValueError(f"Frame() argument must be in the range 0..2, got {val}")
        if _frames is not None:
            return _frames[val]

        # first time
        obj = super(Frame, cls).__new__(cls, val)
        cls._checkFrameValue(obj)
        return obj

    @staticmethod
    def fromPhase(phase):
        """construct a Frame from a GFF/GTF like phase, which maybe an int or str
        '.' or < 0 results in None."""
        if isinstance(phase, str):
            if phase == '.':
                return None
            phase = int(phase)
        if phase < 0:
            return None
        elif phase == 0:
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

    @staticmethod
    def fromFrame(frame):
        """convert from an integer or a string, < 0, '.', or None
        results None.  A Frame object returns itself."""
        if isinstance(frame, Frame) or (frame is None):
            return frame
        if isinstance(frame, str):
            if frame == '.':
                return None
            frame = int(frame)
        if frame < 0:
            return None
        else:
            return Frame(frame)

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


# first-time initialization
FRAME0 = Frame(0)
FRAME1 = Frame(1)
FRAME2 = Frame(2)
_frames = (FRAME0, FRAME1, FRAME2)
