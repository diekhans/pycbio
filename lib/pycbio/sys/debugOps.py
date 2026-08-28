# Copyright 2006-2026 Mark Diekhans
"""Functions useful for debugging"""
import os.path
import sys
import posix
import traceback
from enum import Enum


def lsOpen(msg=None, file=sys.stderr, pid=None):
    """list open files, mostly for debugging"""
    if msg is not None:
        print(msg, file=file)
    if pid is None:
        pid = os.getpid()
    fddir = "/proc/" + str(pid) + "/fd/"
    fds = posix.listdir(fddir)
    fds.sort()
    for fd in fds:
        # entry will be gone for fd dir when it was opened
        fdp = fddir + fd
        if os.path.exists(fdp):
            print("   ", fd, " -> ", os.readlink(fdp), file=file)

def _slotNames(obj):
    "every __slots__ name of the class and its bases, in mro order"
    names = []
    for cls in type(obj).__mro__:
        slots = cls.__dict__.get("__slots__")
        if isinstance(slots, str):
            slots = (slots,)
        if slots is not None:
            names.extend(slots)
    return names

def _objAttrValues(obj):
    """name to value of an object's data attributes, for a class with __dict__,
    __slots__, or both.  vars() alone fails on a __slots__ class."""
    attrs = dict(getattr(obj, "__dict__", {}))
    for name in _slotNames(obj):
        if hasattr(obj, name):
            attrs[name] = getattr(obj, name)
    return attrs

def _prettyPrintRecurse(name, value, seen, indent, level, filter_func, fh):
    if (filter_func is None) or filter_func(name):
        print(' ' * (indent * (level + 1)) + f"{name}=", end="", file=fh)
        _prettyPrint(value, seen, indent, level + 1, filter_func, fh, inline=True)

def _prettyPrint(obj, seen, indent, level, filter_func, fh, *, inline=False):
    if id(obj) in seen:
        print(('' if inline else ' ' * (indent * level)) + "<recursion>", file=fh)
        return
    seen.add(id(obj))
    space = ' ' * (indent * level)
    startsp = '' if inline else space
    if hasattr(obj, "_fields"):  # namedtuple; can't use isinstance
        print(startsp + f"{obj.__class__.__name__}(", file=fh)
        for field in obj._fields:
            _prettyPrintRecurse(field, getattr(obj, field), seen, indent, level, filter_func, fh)
        print(space + ")", file=fh)
    elif isinstance(obj, Enum):
        print(startsp + repr(obj), file=fh)
    elif isinstance(obj, (list, tuple)):
        print(startsp + "[", file=fh)
        for item in obj:
            _prettyPrint(item, seen, indent, level + 1, filter_func, fh=fh)
        print(space + "]", file=fh)
    elif isinstance(obj, dict):
        print(startsp + "{", file=fh)
        for key, value in obj.items():
            _prettyPrintRecurse(repr(key), value, seen, indent, level, filter_func, fh)
        print(space + "}", file=fh)
    elif hasattr(obj, "__dict__") or hasattr(obj, "__slots__"):
        print(startsp + f"{obj.__class__.__name__}(", file=fh)
        for key, value in _objAttrValues(obj).items():
            _prettyPrintRecurse(key, value, seen, indent, level, filter_func, fh)
        print(space + ")", file=fh)
    else:
        print(startsp + repr(obj), file=fh)

    # dropping only this object, not the whole set, allows an object to be
    # output multiple times as long as it isn't on the recursion path
    seen.discard(id(obj))

def prettyPrint(obj, *, label=None, indent=4, fh=sys.stderr, filter_func=None):
    """
    Pretty print a list with each element on its own line, indented.
    Handles nested lists, dictionaries, and objects with attributes.
    If filter_func is specified, it will be passed a field name,
    return false to skip
    """
    if label is not None:
        print(label, file=fh)
    _prettyPrint(obj, set(), indent, 0, filter_func, fh)


def printCurrentStack(msg=None, *, file=sys.stderr):
    "print the stack trace from where called"
    stack_trace = "".join(traceback.format_stack())
    if msg is not None:
        print(msg, file=file)
    print("Stack trace:\n", stack_trace, file=file)


__all__ = [lsOpen.__name__, prettyPrint.__name__, printCurrentStack.__name__]
