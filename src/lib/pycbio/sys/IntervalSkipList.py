"""Implementation of interval skip lists. 

See:
The Interval Skip List: A Data Structure for Finding All Intervals That Overlap a Point
Eric N. Hanson and Theodore Johnson
tr92-016, June 1992
ftp://ftp.cis.ufl.edu/pub/tech-reports/tr92/tr92-016.ps.Z
see also
http://www-pub.cise.ufl.edu/~hanson/IS-lists/
"""
import pycbio.sys.Immutable

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

----------------------------------------------------------------------------------------------------
procedure findIntervals(K,L,S) {
    x := L.header;
    S := empty()
    # Step down to bottom level. 
    for i:=maxLevel down to 1 {
       # Search forward on current level as far as possible.
       while (x->forward[i] != null and x->forward[i]->key < K) do {
           x := x->forward[i]
       }
       # Pick up interval markers on edge when dropping down a level.
       S := S | x->markers[i]
    }

    # Scan forward on bottom level to find location where search key will
    # lie.
    while (x->forward[0] != null and x->forward[0]->key < K) {
        x := x->forward[0];
    }

    # If K is not in list, pick up interval markers on edge, otherwise
    # pick up markers on node with value = K.
    if (x->forward[0] == null or x->forward[0]->key != K) {
        S := S | x->markers[0]
    } else {
        S := S | x->forward[0]->eqMarkers
}


----------------------------------------------------------------------------------------------------
procedure adjustMarkersOnInsert(L,N ,updated) {
   # Update the IS-list L to satisfy the marker invariant.  Input: IS-list L,
   # new node N , vector updated of nodes with updated pointers. The value of
   # updated[i] is a pointer to the node whose level i edge was changed to
   # point to N .

   # Phase 1: place markers on edges leading out of N as needed.
   # Starting at bottom level, place markers on outgoing level i edge of N .
   # If a marker has to be promoted from level i to i+1 or higher, place
   # it in the promoted set at each step.
        
   newPromoted := empty # make set of promoted markers initially empty
   promoted := empty # temporary set to hold newly promoted markers

   for i := 0 to level(N)-2 do {
       for m in updated[i]->markers[i] do {
          if the interval of m contains (N->key,N->forward[i+1]<key) {
             # promote m
             remove m from the level i path from N->forward[i] to N->forward[i+1]
             and add m to newPromoted 
           } else {
             # place m on the level i edge out of N
           }
       }
       for m in promoted do {
         if the interval of m does not contain (N->key,N->forward[i+1]->key)  {
            # m does not need to be promoted higher
            place m on the level i edge out of N and remove m from promoted
         } else{
           # continue to promote m
            remove m from the level i path from N->forward[i] to N->forward[i+1]
         }

         promoted := promoted | newPromoted
         newPromoted := empty
     }

     # Combine the promoted set and updated[level(N )-1]->markers[level(N )-1]
     # and install them as the set of markers on the top edge out of N.
     LN := level(N )-1
     N->markers[LN] := promoted | updated[LN]->markers[LN]

     # Phase 2: adjust markers to the left of N as needed.
     # Markers on edges leading into N may need to be promoted as
     # high as the top edge coming into N , but never higher.

     promoted := empty
     newPromoted := empty

     for i := 0 to level(N )-2 do {
         for each mark m in updated[i]->markers[i] {
             if m needs to be promoted (i.e. m's interval contains (updated[i+1]->key,N->key)) {
                  place m in newPromoted. 
                  remove m from the path of level[i] edges between
                  updated[i+1] and N (it will be on all those edges
                  or else the invariant would have previously been violated).
             }
         for each mark m in promoted do {
             if m belongs at this level, (i.e. m's interval covers (updated[i]->key,N->key)
                  but not (updated[i+1]->key,N->key))
            then place m on the level i edge between updated[i] and N ,
            and remove m from promoted.
           else strip m from the level i path from updated[i+1] to N.
         }
        promoted := promoted | newPromoted
        newPromoted := empty

    # Put all marks in the promoted set on the uppermost edge coming into N .
    top := level(N)-1
    updated[top]->markers[top] := updated[top]->markers[top] | promoted

}
----------------------------------------------------------------------------------------------------
procedure placeMarkers(L,I) {
    # mark non-descending path
    x := search(L,I.left)
    if I contains x->key then add I to x->eqMarkers i := 0

    # start at level 0 and go up
    while (I contains (x!key,x!forward[i]!key)) {
        # find level to put mark on
        while(i 6= level(x)-1 and I contains (x->key,x->forward[i+1]->key) {
            i := i + 1
        }
        # Mark current level i edge since it is the highest edge out of x that contains I.
        add I to x->markers[i]
        x := x!forward[i]
        # Add I to eqMarkers set on node unless currently
        # at right endpoint of I and I doesn't contain
        # right endpoint.
;5B        if I contains x!key then add I to x!eqMarkers end
    }
    # mark non-ascending path
    while(x->key != I.right) {
      # find level to put mark on
      while(i 6= 0 and I does not contain (x!key,x!forward[i]!key) do
        i := i - 1
      # At this point, we can assert that i=0 or I contains (x->key,x->forward[i]->key.
      # In addition, x is between A and B so i=0 implies I contains (x!key,x!forward[i]!key.
      # Hence, the interval must be marked.
      add I to x!markers[i]
      x := x!forward[i]
      if I contains x!key then add I to x!eqMarkers
  }
}
----------------------------------------------------------------------------------------------------
procedure adjustMarkersOnDelete(L,D,updated) 
    demoted := OE newDemoted := OE

    # Phase 1: lower markers on edges to the left of D as needed.
    for i := level(D)-1 down to 0 {
       Find marks on edge into D at level i to be demoted, (which means they don't cover
       the interval (updated[i]!key,D!forward[i]!key)), 
       remove them from that edge, and place them in newDemoted.

      # Note: no marker will ever be removed from a level 0 edge
      # because any interval with a marker on the incoming level 0
      # edge must have a marker on an edge out of D. Hence the 
      # interval for any mark into D on level 0 always contains 
      # (updated[0]!key,D!forward[0]!key).

      for each mark m in demoted set {
          # the steps below won't execute for i=level(D)-1 because demoted is empty.
          Let X be the nearest node prior to D that has more than i levels. 
          Let Y be the nearest node prior to D that has i or more levels
          (Y is updated[i], X is updated[i+1]).
          Place m on each level i edge between X and Y (this may not
          include any edges if X and Y are the same node).
          If this is the lowest level m needs to be placed on (i.e. m covers the interval
          (Y !key,D!forward[i]!key)) then place m on the level i edge out of Y and
          remove m from the demoted set. 
      }
      demoted := demoted | newDemoted
      newDemoted := empty
    }

    # Phase 2: lower markers on edges to the right of D as needed.

    for i := level(D)-1 down to 0 do begin
       for each marker m on the level i edge out of D do
          if the interval of m does not cover (updated[i],D!forward[i])
          then add m to newDemoted.

       for each marker m in demoted do {
           Place m on each edge on the level i path from D!forward[i] to
           D!forward[i+1].
           If the interval of m contains (updated[i]!key,D!forward[i]!key)
           then remove m from demoted.
       }
       demoted := demoted | newDemoted
      newDemoted := empty

}

----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------

    

__all__ = (Entry.__name__, IntervalSkipList.__name__)
