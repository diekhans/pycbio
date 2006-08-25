"operations on strings"
import re

__all__ = ("hasSpaces", "splitAtSpaces")

# matches one or more whitespaces
spaceRe = re.compile("[ \t\n\v\f\r]+")

def hasSpaces(s):
    "test if there are any whitespace characters in a string"
    return spaceRe.search(s) != None

def splitAtSpaces(s):
    "split a string at one or more contiguous whitespaces"
    return spaceRe.split(s)
