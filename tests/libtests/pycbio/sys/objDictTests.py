# Copyright 2006-2018 Mark Diekhans
import unittest
import sys
import pickle
import json
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.objDict import ObjDict, DefaultObjDict
from pycbio.sys.testCaseBase import TestCaseBase
try:
    import jsonpickle
    haveJsonPickle = True
except ModuleNotFoundError:
    haveJsonPickle = False
    print("NOTE: jsonpickle not found, tests disabled", file=sys.stderr)

class TestMixin(object):
    def assertKeyValues(self, expect, od):
        "compare (key, values) to expeccted"
        self.assertEqual(expect, tuple(od.items()))

class ObjDictDerived(ObjDict):
    __slots__ = ()
    pass


simpleJson = """
[
    {
        "one": "value 1",
        "two": "value 2",
        "three": "value 3"
    },
    {
        "four": "value 4",
        "five": "value 5",
        "six": "value 6"
    }
]
"""

nestedJson = """
{
    "fldA":
    {
       "fldB":
       {
            "first": "Fred",
            "last": "Flintstone"
       }
    }
}
"""

def editJsonPicklePath(inJson, outJson):
    "edit py/object entry in json file so it is independent on how this file is loaded"
    # "py/object": "libtests.pycbio.sys.objDictTests.ObjDictDerived",
    # or
    # "py/object": "__main__.ObjDictDerived",
    with open(inJson) as inFh:
        with open(outJson, "w") as outFh:
            for line in inFh:
                line = line.replace("__main__.", "libtests.pycbio.sys.objDictTests.")
                outFh.write(line)


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
        editJsonPicklePath(self.getOutputFile(".json"), self.getOutputFile(".edit.json"))
        self.diffExpected(".edit.json")
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

    def testJsonLoad(self):
        objs = json.loads(simpleJson, object_pairs_hook=ObjDict)
        self.assertTrue(isinstance(objs, list))
        self.assertEqual(2, len(objs))
        obj = objs[0]
        self.assertTrue(isinstance(obj, ObjDict))
        self.assertEqual('value 1', obj['one'])
        self.assertEqual('value 2', obj.two)

    def testRecursiveObjDict(self):
        # ObjDict with dict sub objects being turned into ObjDicts
        obj = json.loads(nestedJson, object_pairs_hook=ObjDict)
        self.assertTrue(isinstance(obj, ObjDict))
        self.assertTrue(isinstance(obj.fldA, ObjDict))
        self.assertTrue(isinstance(obj.fldA.fldB, ObjDict))
        fldB = obj.fldA.fldB
        self.assertEqual(fldB.first, "Fred")
        self.assertEqual(fldB.last, "Flintstone")


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

    def testPickle(self):
        self._runPickleTest(DefaultObjDict(list))

    def _runJsonPickleTest(self, od):
        self._initObjDict(od)

        with open(self.getOutputFile(".json"), 'w') as fh:
            print(jsonpickle.encode(od, indent=4), file=fh)
        editJsonPicklePath(self.getOutputFile(".json"), self.getOutputFile(".edit.json"))
        self.diffExpected(".edit.json")

        with open(self.getOutputFile(".json")) as fh:
            od2 = jsonpickle.decode(fh.read())
        self.assertTrue(isinstance(od2, DefaultObjDict))
        self._checkObjDict(od2)

    def X_testJsonPickle(self):
        if haveJsonPickle:
            self._runJsonPickleTest(DefaultObjDict(list))

    def testJsonLoad(self):
        objs = json.loads(simpleJson, object_pairs_hook=DefaultObjDict.jsonHook(list))
        self.assertTrue(isinstance(objs, list))
        self.assertEqual(2, len(objs))
        obj = objs[0]
        self.assertTrue(isinstance(obj, DefaultObjDict))
        self.assertEqual('value 1', obj['one'])
        self.assertEqual('value 2', obj.two)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(ObjDictTests))
    ts.addTest(unittest.makeSuite(DefaultObjDictTests))
    return ts


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
