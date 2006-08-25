"""Miscellaneous type operations"""

__all__ = ("isListLike", "isIterable")

def isListLike(v):
    "is variable a list or tuple?"
    return isinstance(v, list) or isinstance(v, tuple)

# FIXME: bad name, as strings are iterable
def isIterable(v):
    "is variable a list, tuple, or set?"
    return isinstance(v, list) or isinstance(v, tuple) or isinstance(v, set)
