# Copyright 2006-2012 Mark Diekhans
"""Miscellaneous operations on sets"""

# FIXME: should not need `set' as part of function names, since qualified by
# module. move mkset from typeOps.
from . import typeOps


def setJoin(s, sep=" "):
    "join a set into a sorted string, converting each element to a string"
    return sep.join(sorted([str(e) for e in s]))


def itemsInSet(seq, setFilter):
    "generator over all elements of sequence that are in the setFilter"
    for item in seq:
        if item in setFilter:
            yield item


def mkfzset(item):
    """create a frozenset from item.  If it's None, return an empty set, if
    it's iterable, convert to a set, if it's a single item, make a set of it,
    it it's already a frozenset, just return as-is"""
    if isinstance(item, frozenset):
        return item
    elif isinstance(item, set):
        return frozenset(item)
    elif item is None:
        return frozenset()
    elif typeOps.isIterable(item):
        return frozenset(item)
    else:
        return frozenset([item])
