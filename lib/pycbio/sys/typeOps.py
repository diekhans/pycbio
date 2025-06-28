# Copyright 2006-2025 Mark Diekhans
"""Miscellaneous type operations"""
# FIXME: move to other modules or move set stuff in here.
from collections import abc
from pycbio import PycbioException

def isListLike(obj):
    "is variable a list-lile, but not a string?"
    return isinstance(obj, abc.Sequence) and (not isinstance(obj, str))

def isIterable(obj):
    "is variable a iterable, but not a string"
    return isinstance(obj, abc.Iterable) and (not isinstance(obj, str))

def listAppend(lst, item):
    """if lst is None, create a new list with item, otherwise append item.
    Returns list"""
    if lst is None:
        return [item]
    else:
        lst.append(item)
    return lst


def listExtend(lst, items):
    """if lst is None, create a new list with items, otherwise extend with items.
    Returns list"""
    if lst is None:
        return list(items)
    else:
        lst.extend(items)
    return lst


def mkiter(item):
    """create a iterator over item, if item is iterable, just return an iter,
    if item is not iterable or is a string, create an iterable to return just
    item, if item is none, return an empty iter"""
    # FIXME: don't really need to construct a list
    if item is None:
        return iter(())
    elif isIterable(item):
        return iter(item)
    else:
        return iter([item])


def mkset(item):
    """create a set from item.  If it's None, return an empty set, if it's
    iterable, convert to a set, if it's a single item, make a set of it,
    it it's already a set, just return as-is"""
    # FIXME: move to setOps
    if isinstance(item, set):
        return item
    elif item is None:
        return set()
    elif isIterable(item):
        return set(item)
    else:
        return set([item])


def noneOrZero(v):
    "test if a value is either None or len of zero"
    return (v is None) or (len(v) == 0)


def addUniq(d, k, v):
    "add to a dict, generating an error if the item already exists"
    if k in d:
        raise PycbioException("item \"{}\" already in dict".format(str(k)))
    d[k] = v


def dictObtain(d, key, mkFunc):
    "return entry d[key], creating with mkFunc if it doesn't exist"
    if key not in d:
        e = d[key] = mkFunc()
    else:
        e = d[key]
    return e


def _annonStr(self):
    "__str__ function for annon objects"
    return ", ".join(["{}={}".format(k, repr(getattr(self, k))) for k in sorted(dir(self)) if not k.startswith("__")])


def annon(**kwargs):
    """create an anonymous object with fields that are same as the keyword
    arguments.  This is different from a named tuple as it create an object without
    defining a class.
    """
    kwargs.update({"__str__": _annonStr})
    return type('', (), kwargs)()


def attrdict(obj):
    """Create a dictionary of all attributes in an object. This will work for
    classes with __slots__ or __dict__.    The returned object may or may not be the
    object and so should *not be modified*"""
    try:
        return vars(obj)
    except TypeError:
        return {a: getattr(obj, a) for a in dir(obj)}


# Cache for instance to dict of memoized properties. It is keyed by object id
# and each value is a dict with method name mapped to value
_memo_cache = dict()

def _obtain_memo_cache_entry(obj):
    objid = id(obj)
    entry = _memo_cache.get(objid)
    if entry is None:
        entry = _memo_cache[objid] = {}
    return entry

def cached_immutable_property(method):
    """
    This works like functools.cached_property, however
    it can be used with a class that is immutable, particular
    namedtuple based class

    The should also be a __del__ function that calls
    cached_immutable_property_free(self).
    """
    def wrapper(self):
        entry = _obtain_memo_cache_entry(self)
        # must check, as memo value could be None
        if method.__name__ in entry:
            return entry[method.__name__]
        else:
            value = entry[method.__name__] = method(self)
            return value
    return property(wrapper)

def cached_immutable_property_free(obj):
    """free memoized values for the object.  Call from __del__"""
    if id(obj) in _memo_cache:
        del _memo_cache[id(obj)]
