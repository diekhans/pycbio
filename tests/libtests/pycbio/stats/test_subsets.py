# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.stats.subsets import Subsets

testSet = frozenset(("A", "B", "C"))
testSet2 = frozenset(("A", "B", "C", "D"))

def testGetSubsets():
    expectSet = ((frozenset(("A",)),
                  frozenset(("B",)),
                  frozenset(("C",)),
                  frozenset(("A", "B",)),
                  frozenset(("A", "C",)),
                  frozenset(("B", "C",)),
                  frozenset(("A", "B", "C"))))

    subsets = Subsets(testSet)
    ss = subsets.getSubsets()
    assert ss == expectSet

def testGetInclusizeSubsets():
    expectSet = ((frozenset(("A",)),
                  frozenset(("C",)),
                  frozenset(("A", "C",))))
    subsets = Subsets(testSet)
    iss = subsets.getInclusiveSubsets(frozenset(("A", "C",)))
    assert iss == expectSet

def testGetInclusizeSubsets2():
    expectSet = (frozenset(('A',)),
                 frozenset(('C',)),
                 frozenset(('D',)),
                 frozenset(('A', 'C')),
                 frozenset(('A', 'D')),
                 frozenset(('C', 'D')),
                 frozenset(('A', 'C', 'D')))
    subsets = Subsets(testSet)
    iss = subsets.getInclusiveSubsets(frozenset(("A", "C", "D")))
    assert iss == expectSet
