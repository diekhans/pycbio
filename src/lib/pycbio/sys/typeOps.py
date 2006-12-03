"""Miscellaneous type operations"""

def isListLike(v):
    "is variable a list or tuple?"
    return isinstance(v, list) or isinstance(v, tuple)

# FIXME: bad name, as strings are iterable
def isIterable(v):
    "is variable a list, tuple, or set?"
    return isinstance(v, list) or isinstance(v, tuple) or isinstance(v, set)

__all__ = (isListLike.__name__, isIterable.__name__)

