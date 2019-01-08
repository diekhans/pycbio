# Copyright 2006-2018 Mark Diekhans
# Copyright of original unknown (https://goodcode.io/articles/python-dict-object/)

# default dictionary with keys as object files, based on:
# https://goodcode.io/articles/python-dict-object/
from collections import defaultdict

class DefaultObjDict(defaultdict):
    """defaultdict-based object where keys are field names"""

    def __init__(self, dtype):
        defaultdict.__init__(self, dtype)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)
