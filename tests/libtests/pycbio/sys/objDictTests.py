# Copyright 2006-2018 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.objDict import ObjDict
from pycbio.sys.defaultObjDict import DefaultObjDict
from pycbio.sys.testCaseBase import TestCaseBase

class TestMixin(object):
    def assertKeyValues(self, expect, od):
        "gets sort tuple of (key values) and compare"
        keyValues = [(k, od[k]) for k in list(od.keys())]
        keyValues.sort(key=lambda kv: kv[0])
        keyValues = tuple(keyValues)
        self.assertEqual(expect, keyValues)


class ObjDictTests(TestCaseBase, TestMixin):
    def testBasic(self):
        od = ObjDict()
        od.one = "value 1"
        od["two"] = "value 2"
        od.three = "value 3"
        keys = list(od.keys())
        keys.sort()
        self.assertKeyValues((('one', 'value 1'), ('three', 'value 3'), ('two', 'value 2')), od)

        od.two = "value 2.1"
        self.assertKeyValues((('one', 'value 1'), ('three', 'value 3'), ('two', 'value 2.1')), od)

        del od.two
        self.assertKeyValues((('one', 'value 1'), ('three', 'value 3')), od)

        self.assertEqual("value 1", od.one)


class DefaultObjDictTests(TestCaseBase, TestMixin):
    def testList(self):
        od = DefaultObjDict(list)
        od.one.append("value 1.1")
        od["two"].append("value 2.1")
        keys = list(od.keys())
        keys.sort()
        self.assertKeyValues((('one', ['value 1.1']), ('two', ['value 2.1'])), od)

        od.two.append("value 2.2")
        self.assertKeyValues((('one', ['value 1.1']), ('two', ['value 2.1', 'value 2.2'])), od)

        del od.two
        self.assertKeyValues((('one', ['value 1.1']),), od)

        self.assertEqual("value 1.1", od.one[0])


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ObjDict))
    return ts


if __name__ == '__main__':
    unittest.main()
