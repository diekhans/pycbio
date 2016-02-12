"""
Sequence Intervals
"""
import copy
from pycbio.bio.bio import convert_strand, reverse_complement


class ChromosomeInterval(object):
    """
    Represents an interval of a chromosome. BED coordinates, strand is True,
    False or None (if no strand)
    interval arithmetic adapted from http://code.activestate.com/recipes/576816-interval/
    """
    __slots__ = ('chromosome', 'start', 'stop', 'strand')    # conserve memory

    def __init__(self, chromosome, start, stop, strand):
        self.chromosome = str(chromosome)
        assert start <= stop
        self.start = int(start)    # 0 based
        self.stop = int(stop)      # exclusive
        if strand not in [True, False, None]:
            strand = convert_strand(strand)
        self.strand = strand       # True or False

    def __len__(self):
        return abs(self.stop - self.start)

    def __hash__(self):
        return (hash(self.chromosome) ^ hash(self.start) ^ hash(self.stop) ^ hash(self.strand) ^
                hash((self.chromosome, self.start, self.stop, self.strand)))

    def __eq__(self, other):
        return (isinstance(other, type(self)) and
                (self.chromosome, self.start, self.stop, self.strand) ==
                (other.chromosome, other.start, other.stop, other.strand))

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return (isinstance(other, type(self)) and self.chromosome == other.chromosome and
                (self.start, self.stop) > (other.start, other.stop))

    def __ge__(self, other):
        return (isinstance(other, type(self)) and self.chromosome == other.chromosome and
                (self.start, self.stop) >= (other.start, other.stop))

    def __lt__(self, other):
        return (isinstance(other, type(self)) and self.chromosome == other.chromosome and
                (self.start, self.stop) < (other.start, other.stop))

    def __le__(self, other):
        return (isinstance(other, type(self)) and self.chromosome == other.chromosome and
                (self.start, self.stop) <= (other.start, other.stop))

    def __contains__(self, other):
        return self.start <= other < self.stop

    def __add__(self, other):
        if self.strand != other.strand or self.chromosome != other.chromosome:
            return None
        return ChromosomeInterval(self.chromosome, self.start + other.start, self.stop + other.stop, self.strand)

    def __sub__(self, other):
        if self.strand != other.strand or self.chromosome != other.chromosome:
            return None
        return ChromosomeInterval(self.chromosome, self.start - other.start, self.stop - other.stop, self.strand)

    @property
    def is_null(self):
        if len(self) == 0:
            return True
        return False

    def intersection(self, other):
        """
        returns a new ChromosomeInterval representing the overlap between these intervals
        returns None if there is no overlap
        """
        if self.strand != other.strand or self.chromosome != other.chromosome:
            return None
        if self > other:
            other, self = self, other
        if self.stop <= other.start:
            return None
        if self == other:
            return self
        if self.stop <= other.stop:
            return ChromosomeInterval(self.chromosome, other.start, self.stop, self.strand)
        else:
            return ChromosomeInterval(self.chromosome, other.start, other.stop, self.strand)

    def complement(self, size):
        """
        returns two new ChromosomeIntervals representing the complement of this interval.
        Requires a input chromosome size
        """
        return [ChromosomeInterval(self.chromosome, 0, self.start, self.strand),
                ChromosomeInterval(self.chromosome, self.stop, size, self.strand)]

    def union(self, other):
        """
        Returns either one or two ChromosomeIntervals representing the union of this interval with the other.
        If two are returned, that means the two intervals do not overlap.
        Returns None if the intervals are not on the same strand and chromosome
        """
        if self.chromosome != other.chromosome:
            return None
        if self > other:
            other, self = self, other
        if self == other:
            return self
        if self.intersection(other) is not None:
            return self.hull(other)
        else:
            return [self, other]

    def hull(self, other):
        """
        Returns a new ChromosomeInterval representing the merged interval of these two, regardless of overlap
        I.E. if one interval is [1, 10) and another is [20, 30) this will return [1, 30)
        """
        if self.chromosome != other.chromosome:
            return None
        if self > other:
            other, self = self, other
        if self.subset(other):
            return ChromosomeInterval(self.chromosome, other.start, other.stop, self.strand)
        elif other.subset(self):
            return ChromosomeInterval(self.chromosome, self.start, self.stop, self.strand)
        return ChromosomeInterval(self.chromosome, self.start, other.stop, self.strand)

    def overlap(self, other):
        """
        Returns True if this interval overlaps other (if they are on the same strand and chromosome)
        """
        if self.chromosome != other.chromosome:
            return False
        if self > other:
            other, self = self, other
        return self.stop > other.start

    def subset(self, other):
        """
        Returns True if this interval is a subset of the other interval (if they are on the same strand and chromosome)
        """
        if self.chromosome != other.chromosome:
            return False
        return self.start >= other.start and self.stop <= other.stop

    def proper_subset(self, other):
        """
        same a subset, but only if other is entirely encased in this interval.
        """
        if self.chromosome != other.chromosome:
            return False
        return self.start > other.start and self.stop < other.stop

    def separation(self, other):
        """
        Returns a integer representing the start distance between these intervals
        """
        if self.chromosome != other.chromosome:
            return None
        if self > other:
            other, self = self, other
        if self.stop > other.start:
            return 0
        else:
            return other.start - self.stop

    def symmetric_separation(self, other):
        """
        Returns a pair of distances representing the symmetric distance between two intervals
        """
        if self.chromosome != other.chromosome:
            return None
        if self > other:
            other, self = self, other
        return other.start - self.start, other.stop - self.stop

    def get_bed(self, rgb, name):
        """
        Returns BED tokens representing this interval. Requires a name and a rgb value. BED is BED12.
        """
        return [self.chromosome, self.start, self.stop, name, 0, convert_strand(self.strand), self.start, self.stop,
                rgb, 1, len(self), 0]

    def get_sequence(self, seq_dict, strand=True):
        """
        Returns the sequence for this intron in transcript orientation (reverse complement as necessary)
        If strand is False, returns the + strand regardless of transcript orientation.
        """
        if strand is False or self.strand is True:
            return seq_dict[self.chromosome][self.start:self.stop]
        if self.strand is False:
            return reverse_complement(seq_dict[self.chromosome][self.start:self.stop])
        assert False

    def __repr__(self):
        return "ChromosomeInterval('{}', {}, {}, '{}')".format(self.chromosome, self.start, self.stop,
                                                               convert_strand(self.strand))


def gap_merge_intervals(intervals, gap):
    """
    Merges intervals within gap bases of each other
    """
    new_intervals = []
    for interval in intervals:
        if not new_intervals:
            new_intervals.append(copy.deepcopy(interval))
        elif interval.separation(new_intervals[-1]) <= gap:
            new_intervals[-1] = new_intervals[-1].hull(interval)
        else:
            new_intervals.append(copy.deepcopy(interval))
    return new_intervals


def interval_not_intersect_intervals(intervals, interval):
    """
    Takes a list of intervals and one other interval and determines if interval does not intersect with any of the
    intervals. returns True if this is the case.
    """
    intersections = []
    for target_interval in intervals:
        intersections.append(interval.intersection(target_interval))
    return intersections.count(None) == len(intersections)


def interval_not_within_wiggle_room_intervals(intervals, interval, wiggle_room=0):
    """
    Same thing as intervalNotIntersectIntervals but looks within wiggleRoom bases to count a valid lack of intersection
    """
    separation = [sum(interval.symmetric_separation(target_interval)) for target_interval in intervals]
    return not any([x <= 2 * wiggle_room for x in separation])  # we allow wiggle on both sides
