"""Miscellaneous operations on sets"""

# FIXME: should need `set' as part of function names, since qualified by
# module

def setJoin(s, sep=" "):
    "join a set into a sorted string, converting each element to a string"
    l = []
    for i in s:
        l.append(str(i))
    l.sort()
    return sep.join(l)

def itemsInSet(seq, setFilter):
    "generator over all elements of sequence that are in the setFilter"
    for item in seq:
        if item in setFilter:
            yield item

