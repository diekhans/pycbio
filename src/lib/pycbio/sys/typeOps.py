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

__all__ = (isListLike.__name__, isIterable.__name__, mkiter.__name__, mkset.__name__)

