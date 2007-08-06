"""Implementation of interval skip lists. 

See:
The Interval Skip List: A Data Structure for Finding All Intervals That Overlap a Point
Eric N. Hanson and Theodore Johnson
tr92-016, June 1992
ftp://ftp.cis.ufl.edu/pub/tech-reports/tr92/tr92-016.ps.Z
see also
http://www-pub.cise.ufl.edu/~hanson/IS-lists/
"""

from pycbio.sys.Immutable import Immutable
from pycbio.sys import typeOps

class Entry(Immutable):
    "An entry for an interval and associated value. This is immutable"

    __slots__ = ("start", "end", "val")

    def __init__(self, start, end, val):
        self.start = start
        self.end = end
        self.val = val
        self.makeImmutable()

class Node(object):
    "a node in skip list.

    Fields:
        pos - key for node
        forward - array of forward links
        markers - array of sets of markers
        owners -  intervals that have an endpoint equal to key
        eqMarkers - a set of markers for intervals that have a a marker on an
                    edge that ends on this node,
    "
    def __init__(self, pos):
        self.pos = pos
        self.forward = []
        self.markers = []
        self.owners = set()
        self.eqMarkers = set()


class IntervalSkipList(object):
    "skip list object addressed by interval"
    def __init__(self, maxLevel):
        self.maxLevel = maxLevel
        self.head = Node(None)

    def find(self, start, end):
        "return a set of Value objects overlaping the specified range"
        vals = set()
        # Step down to bottom level
        # Search forward on current level as far as possible.
        while (x->forward[i] != null and x->forward[i]->key < K) do {
            x := x->forward[i]
        }
        # Pick up interval markers on edge when dropping down a level.

        return vals



 
__all__ = (Entry.__name__, IntervalSkipList.__name__)
