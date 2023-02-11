# Copyright 2006-2022 Mark Diekhans
# Copyright of original unknown (https://goodcode.io/articles/python-dict-object/)

# dictionary with keys as object files, based on:
# https://goodcode.io/articles/python-dict-object/
from collections import defaultdict
from functools import partial

def _attributeError(name):
    raise AttributeError("No such attribute: " + name)

class ObjDict(dict):
    """Dict object where keys are field names.
    This is useful for JSON by doing:
       json.load(fh, object_pairs_hook=ObjDict)

    When inserting a dict, it must be explicitly converted to an ObjDict if
    desired.
    """
    __slots__ = ()

    def __getattr__(self, name):
        if not name in self:
            _attributeError(name)
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if not name in self:
            _attributeError(name)
        del self[name]


class DefaultObjDict(defaultdict):
    """defaultdict-based object where keys are field names.
    This is useful for JSON by doing:
       json.load(fh, object_pairs_hook=DefaultObjDict.jsonHook(default_factory))

    When inserting a dict, it must be explicitly converted to an DefaultObjDict or ObjDict if
    desired.
    """
    __slots__ = ()

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if not name in self:
            _attributeError(name)
        del self[name]

    @staticmethod
    def jsonHook(default_factory=None):
        return partial(DefaultObjDict, default_factory)
