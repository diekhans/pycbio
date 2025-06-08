# Copyright 2006-2025 Mark Diekhans
import pytest
import sys
import pickle
import json
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.objDict import ObjDict, DefaultObjDict, defaultObjDictJsonHook
from pycbio.sys import testSupport as ts
try:
    import jsonpickle
    _haveJsonPickle = True
except ModuleNotFoundError:
    _haveJsonPickle = False
    print("NOTE: jsonpickle not found, tests disabled", file=sys.stderr)

class TestMixin:
    def assertKeyValues(self, expect, od):
        "compare (key, values) to expeccted"
        assert tuple(od.items()), expect

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

def _do_json_pickling_test(request, od):
    with open(ts.get_test_output_file(request, ".json"), 'w') as fh:
        print(jsonpickle.encode(od, indent=4), file=fh)
    ts.diff_results_expected(request, ".json")
    with open(ts.get_test_output_file(request, ".json")) as fh:
        return jsonpickle.decode(fh.read())

####
# ObjDict tests
####
def _initObjDict(od):
    od.one = "value 1"
    od["two"] = "value 2"
    od.three = "value 3"

def _checkObjDict(od):
    assert od.one, "value 1"
    assert od["one"], "value 1"
    assert od.two, "value 2"
    assert od["two"], "value 2"
    assert tuple(od.items()) == (('one', 'value 1'), ('two', 'value 2'), ('three', 'value 3'))
    with pytest.raises(AttributeError):
        od.ten

def _runObjDictTest(od):
    _initObjDict(od)
    _checkObjDict(od)

    od.two = "value 2.1"
    assert tuple(od.items()) == (('one', 'value 1'), ('two', 'value 2.1'), ('three', 'value 3'))

    del od.two
    assert tuple(od.items()) == (('one', 'value 1'), ('three', 'value 3'))

def test_base():
    _runObjDictTest(ObjDict())

def test_derived():
    _runObjDictTest(ObjDictDerived())

def _runPickleTest(request, od):
    _initObjDict(od)
    with open(ts.get_test_output_file(request, ".pkl"), 'wb') as fh:
        pickle.dump(od, fh)
    with open(ts.get_test_output_file(request, ".pkl"), 'rb') as fh:
        od2 = pickle.load(fh)
    assert isinstance(od2, od.__class__)
    _checkObjDict(od2)

def test_pickle(request):
    _runPickleTest(request, ObjDict())

def test_pickle_derived(request):
    _runPickleTest(request, ObjDictDerived())

def _run_json_pickle_test(request, od):
    _initObjDict(od)
    od2 = _do_json_pickling_test(request, od)
    assert isinstance(od2, ObjDict)
    _checkObjDict(od2)

@pytest.mark.skipif(not _haveJsonPickle, reason="jsonpickle not installed")
def test_json_pickle(request):
    _run_json_pickle_test(request, ObjDict())

@pytest.mark.skipif(not _haveJsonPickle, reason="jsonpickle not installed")
def test_json_pickle_derived(request):
    _run_json_pickle_test(request, ObjDictDerived())

def test_json_load():
    objs = json.loads(simpleJson, object_pairs_hook=ObjDict)
    assert isinstance(objs, list)
    assert 2, len(objs)
    obj = objs[0]
    assert isinstance(obj, ObjDict)
    assert 'value 1', obj['one']
    assert 'value 2', obj.two

def test_recursive_obj_dict():
    # ObjDict with dict sub objects being turned into ObjDicts
    obj = json.loads(nestedJson, object_pairs_hook=ObjDict)
    assert isinstance(obj, ObjDict)
    assert isinstance(obj.fldA, ObjDict)
    assert isinstance(obj.fldA.fldB, ObjDict)
    fldB = obj.fldA.fldB
    assert fldB.first, "Fred"
    assert fldB.last, "Flintstone"

####
# DefaultObjDict tests
####
def _initDefaultObjDict(od):
    od.one.append("value 1.1")
    od["two"].append("value 2.1")

def _checkDefaultObjDict(od):
    assert od.one, ["value 1.1"]
    assert od["one"], ["value 1.1"]
    assert od.two, ["value 2.1"]
    assert od["two"], ["value 2.1"]
    assert tuple(od.items()) == (('one', ['value 1.1']), ('two', ['value 2.1']))

def _runDefaultObjDictTest(od):
    _initDefaultObjDict(od)
    _checkDefaultObjDict(od)

    od.two.append("value 2.2")
    assert tuple(od.items()) == (('one', ['value 1.1']), ('two', ['value 2.1', 'value 2.2']))

    del od.two
    assert tuple(od.items()) == (('one', ['value 1.1']),)

    assert "value 1.1", od.one[0]
    assert od.ten == []    # creates default

def test_default_list():
    _runDefaultObjDictTest(DefaultObjDict(list))

def _runDefaultPickleTest(request, od):
    _initDefaultObjDict(od)
    with open(ts.get_test_output_file(request, ".pkl"), 'wb') as fh:
        pickle.dump(od, fh)
    with open(ts.get_test_output_file(request, ".pkl"), 'rb') as fh:
        od2 = pickle.load(fh)
    assert isinstance(od2, DefaultObjDict)
    _checkDefaultObjDict(od2)

def test_default_pickle(request):
    _runDefaultPickleTest(request, DefaultObjDict(list))

def _runDefaultJsonPickleTest(request, od):
    _initDefaultObjDict(od)
    od2 = _do_json_pickling_test(request, od)
    assert isinstance(od2, DefaultObjDict)
    _checkDefaultObjDict(od2)

# @pytest.mark.skipif(not _haveJsonPickle, reason="jsonpickle not installed")
def X_test_default_json_pickle(request):
    # FIXME: sees issues for why this is disabled
    _runDefaultJsonPickleTest(request, DefaultObjDict(list))

def test_default_json_load():
    objs = json.loads(simpleJson, object_pairs_hook=defaultObjDictJsonHook(list))
    assert isinstance(objs, list)
    assert 2, len(objs)
    obj = objs[0]
    assert isinstance(obj, DefaultObjDict)
    assert 'value 1', obj['one']
    assert 'value 2', obj.two
