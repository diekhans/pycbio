# Copyright 2006-2025 Mark Diekhans
"operations on strings"
import re

# matches one or more whitespaces
spaceRegexp = re.compile("[ \t\n\v\f\r]+")


def hasSpaces(s):
    "test if there are any whitespace characters in a string"
    return spaceRegexp.search(s) is not None


def splitAtSpaces(s):
    "split a string at one or more contiguous whitespaces"
    return spaceRegexp.split(s)


def dup(n, s):
    "make a string with n copies of s"
    lst = []
    for i in range(n):
        lst.append(s)
    return "".join(lst)


def emptyOrNone(s):
    "is a string empty of None"
    return (s is None) or (len(s) == 0)


def emptyForNone(s):
    "return an empty string if s is None, else s"
    return "" if s is None else s


def noneForEmpty(s):
    "return non if s is a empty string, else s"
    return None if s == "" else s


__all__ = (hasSpaces.__name__, splitAtSpaces.__name__, dup.__name__, emptyForNone.__name__, noneForEmpty.__name__)
