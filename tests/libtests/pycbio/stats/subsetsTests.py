# Copyright 2006-2012 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.stats.subsets import Subsets
from pycbio.sys.testCaseBase import TestCaseBase


class SubsetsTests(TestCaseBase):
    testSet = frozenset(("A", "B", "C"))
    testSet2 = frozenset(("A", "B", "C", "D"))

    def testGetSubsets(self):
        expectSet = ((frozenset(("A",)),
                      frozenset(("B",)),
                      frozenset(("C",)),
                      frozenset(("A", "B",)),
                      frozenset(("A", "C",)),
                      frozenset(("B", "C",)),
                      frozenset(("A", "B", "C"))))

        subsets = Subsets(SubsetsTests.testSet)
        ss = subsets.getSubsets()
        self.assertEqual(ss, expectSet)

    def testGetInclusizeSubsets(self):
        expectSet = ((frozenset(("A",)),
                      frozenset(("C",)),
                      frozenset(("A", "C",))))
        subsets = Subsets(SubsetsTests.testSet)
        iss = subsets.getInclusiveSubsets(frozenset(("A", "C",)))
        self.assertEqual(iss, expectSet)

    def testGetInclusizeSubsets2(self):
        expectSet = (frozenset(('A',)),
                     frozenset(('C',)),
                     frozenset(('D',)),
                     frozenset(('A', 'C')),
                     frozenset(('A', 'D')),
                     frozenset(('C', 'D')),
                     frozenset(('A', 'C', 'D')))
        subsets = Subsets(SubsetsTests.testSet)
        iss = subsets.getInclusiveSubsets(frozenset(("A", "C", "D")))
        self.assertEqual(iss, expectSet)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(SubsetsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
