# Copyright 2006-2011 Mark Diekhans
"operations on strings"
import re

# matches one or more whitespaces
spaceRe = re.compile("[ \t\n\v\f\r]+")

def hasSpaces(s):
    "test if there are any whitespace characters in a string"
    return spaceRe.search(s) != None

def splitAtSpaces(s):
    "split a string at one or more contiguous whitespaces"
    return spaceRe.split(s)

def dup(n, s):
    "make a string with n copies of s"
    l = []
    for i in xrange(n):
        l.append(s)
    return "".join(l)

__all__ = (hasSpaces.__name__, splitAtSpaces.__name__, dup.__name__)

