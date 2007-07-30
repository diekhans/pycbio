"""Miscellaneous type operations"""

def isListLike(v):
    "is variable a list or tuple?"
    return isinstance(v, list) or isinstance(v, tuple)

# FIXME: bad name, as strings are iterable
def isIterable(v):
    "is variable a list, tuple, set, or hash? str doesn't count"
    return isinstance(v, list) or isinstance(v, tuple) or isinstance(v, set) or isinstance(v, dict)

def mkiter(item):
    """create a iterator over item, if item is iterable, just return an iter,
    if item is not iterable or is a string, create an iterable to return just
    item, if item is none, return an empty iter"""
    if item == None:
        return iter([])
    elif isIterable(item):
        return iter(item)
    else:
        return iter([item])

def mkset(item):
    """create a set from item.  If it's None, return an empty set, if it's
    iterable, convert to a set, if it's a single item, make a set of it,
    it it's already a set, just return as-is"""
    if isinstance(item, set):
        return item
    elif item == None:
        return set()
    elif isIterable(item):
        return set(item)
    else:
        return set([item])

def noneOrZero(v):
    "test if a value is either None or len of zero"
    return (v == None) or (len(v) == 0)

def addUniq(d, k, v):
    "add to a dict, generating an error if the item already exists"
    if k in d:
        raise Exception("item \"" + str(k) + "\" already in dict")
    d[k] = v

def sortedKeys(d, sortFunc=cmp):
    "return of keys for dict d, sort by sortFunc, if d is None, return an empty list"
    if d == None:
        return []
    else:
        keys = list(d.iterkeys())
        keys.sort(sortFunc)
        return keys

__all__ = (isListLike.__name__, isIterable.__name__, mkiter.__name__, mkset.__name__, noneOrZero.__name__, addUniq.__name__, sortedKeys.__name__)

