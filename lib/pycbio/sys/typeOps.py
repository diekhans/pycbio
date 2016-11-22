# Copyright 2006-2012 Mark Diekhans
"""Miscellaneous type operations"""

# FIXME: move to other modules


def isListLike(v):
    "is variable a list or tuple?"
    return isinstance(v, list) or isinstance(v, tuple)


def listInit(size, val):
    "create a list of length size, with each element containing val"
    l = []
    for i in xrange(size):
        l.append(val)
    return l


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


def isIterable(v):
    "is variable a list, tuple, set, or hash? str doesn't count"
    # FIXME: bad name, as strings are iterable
    return isinstance(v, list) or isinstance(v, tuple) or isinstance(v, set) or isinstance(v, dict)


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
        raise Exception("item \"" + str(k) + "\" already in dict")
    d[k] = v


def dictObtain(d, key, mkFunc):
    "return entry d[key], creating with mkFunc if it doesn't exist"
    if key not in d:
        e = d[key] = mkFunc()
    else:
        e = d[key]
    return e


def sorted(iterable, cmp=None, key=None, reverse=False):
    "create new list from iterable and sort it"
    l = list(iterable)
    l.sort(cmp=cmp, key=key, reverse=reverse)
    return l


def sortedKeys(d, sortFunc=cmp):
    "return of keys for dict d, sort by sortFunc, if d is None, return an empty list"
    if d is None:
        return []
    else:
        keys = list(d.iterkeys())
        keys.sort(cmp=sortFunc)
        return keys


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
    classes with __slots__.  The returned object may or may not be the
    __dict__, and so should not be modified"""
    try:
        return obj.__dict__
    except AttributeError:
        return {a: getattr(obj, a) for a in dir(obj)}

__all__ = (isListLike.__name__, listInit.__name__, listAppend.__name__,
           isIterable.__name__, mkiter.__name__, mkset.__name__,
           noneOrZero.__name__, addUniq.__name__, dictObtain.__name__,
           sorted.__name__, sortedKeys.__name__, annon.__name__,
           attrdict.__name__)
