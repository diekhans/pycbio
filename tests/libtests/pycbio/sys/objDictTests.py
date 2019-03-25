# Copyright 2006-2018 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.objDict import ObjDict, OrderedObjDict, DefaultObjDict
from pycbio.sys.testCaseBase import TestCaseBase

class TestMixin(object):
    def assertKeyValues(self, expect, od):
        "gets sort tuple of (key values) and compare"
        keyValues = [(k, od[k]) for k in list(od.keys())]
        keyValues.sort(key=lambda kv: kv[0])
        keyValues = tuple(keyValues)
        self.assertEqual(expect, keyValues)

    def sharedBasic(self, od):
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

        with self.assertRaises(AttributeError):
            od.ten

class ObjDictTests(TestCaseBase, TestMixin):
    def testBasic(self):
        od = ObjDict()
        self.sharedBasic(od)


class OrderedObjDictTests(TestCaseBase, TestMixin):
    def testBasic(self):
        od = OrderedObjDict()
        self.sharedBasic(od)

    def testOrder(self):
        od = OrderedObjDict(B=1, A=2, C=3, D=4)
        self.assertEqual(list(od.keys()), ['B', 'A', 'C', 'D'])
        self.assertEqual(list(od.values()), [1, 2, 3, 4])
        od.F = 5
        self.assertEqual(list(od.keys()), ['B', 'A', 'C', 'D', 'F'])
        self.assertEqual(list(od.values()), [1, 2, 3, 4, 5])

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

        self.assertEqual(od.ten, [])

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ObjDictTests))
    ts.addTest(unittest.makeSuite(OrderedObjDictTests))
    ts.addTest(unittest.makeSuite(DefaultObjDictTests))
    return ts


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
