# Copyright 2006-2018 Mark Diekhans
import unittest
import sys
import pickle
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.objDict import ObjDict, DefaultObjDict
from pycbio.sys.testCaseBase import TestCaseBase
try:
    import jsonpickle
    haveJsonPickle = True
except:
    haveJsonPickle = False
    print("NOTE: jsonpickle not found, tests disabled", file=sys.stderr)

class TestMixin(object):
    def assertKeyValues(self, expect, od):
        "compare (key, values) to expeccted"
        self.assertEqual(expect, tuple(od.items()))

class ObjDictDerived(ObjDict):
    __slots__ = ()
    pass


class ObjDictTests(TestCaseBase, TestMixin):
    def _initObjDict(self, od):
        od.one = "value 1"
        od["two"] = "value 2"
        od.three = "value 3"

    def _checkObjDict(self, od):
        self.assertEqual(od.one, "value 1")
        self.assertEqual(od["one"], "value 1")
        self.assertEqual(od.two, "value 2")
        self.assertEqual(od["two"], "value 2")
        self.assertKeyValues((('one', 'value 1'), ('two', 'value 2'), ('three', 'value 3')), od)
        with self.assertRaises(AttributeError):
            od.ten

    def _runTest(self, od):
        self._initObjDict(od)
        self._checkObjDict(od)

        od.two = "value 2.1"
        self.assertKeyValues((('one', 'value 1'), ('two', 'value 2.1'), ('three', 'value 3')), od)

        del od.two
        self.assertKeyValues((('one', 'value 1'), ('three', 'value 3')), od)

    def testBase(self):
        self._runTest(ObjDict())

    def testDerived(self):
        self._runTest(ObjDictDerived())

    def _runPickleTest(self, od):
        self._initObjDict(od)
        with open(self.getOutputFile(".pkl"), 'wb') as fh:
            pickle.dump(od, fh)
        with open(self.getOutputFile(".pkl"), 'rb') as fh:
            od2 = pickle.load(fh)
        self.assertTrue(isinstance(od2, od.__class__))
        self._checkObjDict(od2)

    def testPickle(self):
        self._runPickleTest(ObjDict())

    def testPickleDerived(self):
        self._runPickleTest(ObjDictDerived())

    def _runJsonPickleTest(self, od):
        self._initObjDict(od)
        with open(self.getOutputFile(".json"), 'w') as fh:
            print(jsonpickle.encode(od, indent=4), file=fh)
        self.diffExpected(".json")
        with open(self.getOutputFile(".json")) as fh:
            od2 = jsonpickle.decode(fh.read())
        self.assertTrue(isinstance(od2, ObjDict))
        self._checkObjDict(od2)

    def testJsonPickle(self):
        if haveJsonPickle:
            self._runJsonPickleTest(ObjDict())

    def testJsonPickleDerived(self):
        if haveJsonPickle:
            self._runJsonPickleTest(ObjDictDerived())


class DefaultObjDictTests(TestCaseBase, TestMixin):
    def _initObjDict(self, od):
        od.one.append("value 1.1")
        od["two"].append("value 2.1")

    def _checkObjDict(self, od):
        self.assertEqual(od.one, ["value 1.1"])
        self.assertEqual(od["one"], ["value 1.1"])
        self.assertEqual(od.two, ["value 2.1"])
        self.assertEqual(od["two"], ["value 2.1"])
        self.assertKeyValues((('one', ['value 1.1']), ('two', ['value 2.1'])), od)

    def _runTest(self, od):
        self._initObjDict(od)
        self._checkObjDict(od)

        od.two.append("value 2.2")
        self.assertKeyValues((('one', ['value 1.1']), ('two', ['value 2.1', 'value 2.2'])), od)

        del od.two
        self.assertKeyValues((('one', ['value 1.1']),), od)

        self.assertEqual("value 1.1", od.one[0])
        self.assertEqual(od.ten, [])

    def testList(self):
        self._runTest(DefaultObjDict(list))

    def _runPickleTest(self, od):
        self._initObjDict(od)
        with open(self.getOutputFile(".pkl"), 'wb') as fh:
            pickle.dump(od, fh)
        with open(self.getOutputFile(".pkl"), 'rb') as fh:
            od2 = pickle.load(fh)
        self.assertTrue(isinstance(od2, DefaultObjDict))
        self._checkObjDict(od2)

    # FIXME: pickle of DefaultObjDict doesn't work
    def X_testPickle(self):
        self._runPickleTest(ObjDict())

    def _runJsonPickleTest(self, od):
        self._initObjDict(od)

        with open(self.getOutputFile(".json"), 'w') as fh:
            print(jsonpickle.encode(od, indent=4), file=fh)
        self.diffExpected(".json")

        with open(self.getOutputFile(".json")) as fh:
            od2 = jsonpickle.decode(fh.read())
        self.assertTrue(isinstance(od2, DefaultObjDict))
        self._checkObjDict(od2)

    # FIXME: pickle of DefaultObjDict doesn't work
    def X_testJsonPickle(self):
        if haveJsonPickle:
            self._runJsonPickleTest(DefaultObjDict(list))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ObjDictTests))
    ts.addTest(unittest.makeSuite(DefaultObjDictTests))
    return ts


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
