# Copyright 2006-2018 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.objDict import ObjDict
from pycbio.sys.testCaseBase import TestCaseBase


class ObjDictTests(TestCaseBase):

    def _assertKeyValues(self, expect, od):
        "gets sort tuple of (key values) and compare"
        keyValues = [(k, od[k]) for k in list(od.keys())]
        keyValues.sort(key=lambda kv: kv[0])
        keyValues = tuple(keyValues)
        self.assertEqual(keyValues, expect)

    def testBasic(self):
        od = ObjDict()
        od.one = "value 1"
        od["two"] = "value 2"
        od.three = "value 3"
        keys = list(od.keys())
        keys.sort()
        self._assertKeyValues((('one', 'value 1'), ('three', 'value 3'), ('two', 'value 2')), od)

        od.two = "value 2.1"
        self._assertKeyValues((('one', 'value 1'), ('three', 'value 3'), ('two', 'value 2.1')), od)

        del od.two
        self._assertKeyValues((('one', 'value 1'), ('three', 'value 3')), od)

        self.assertEqual("value 1", od.one)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ObjDict))
    return ts


if __name__ == '__main__':
    unittest.main()
