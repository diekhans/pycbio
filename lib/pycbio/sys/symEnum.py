# Copyright 2006-2014 Mark Diekhans
# for python2, requires enum34: https://pypi.python.org/pypi/enum34

from __future__ import print_function
import six
from enum import Enum, EnumMeta
from functools import total_ordering

SymEnum = None  # class defined after use


class SymEnumValue(object):
    "Class used to define SymEnum member that have additional attributes."
    __slots__ = ("value", "externalName")

    def __init__(self, value, externalName=None):
        self.value = value
        self.externalName = externalName


class _SysEnumExternalNameMap(object):
    "Mapping between internal and external member names"
    __slots__ = ("internalToExternal", "externalToInternal")

    def __init__(self):
        self.internalToExternal = {}
        self.externalToInternal = {}

    def add(self, internalName, externalName):
        self.internalToExternal[internalName] = externalName
        self.externalToInternal[externalName] = internalName

    def toExternalName(self, internalName):
        "return name unchanged if no mapping"
        return self.internalToExternal.get(internalName, internalName)

    def toInternalName(self, externalName):
        "return name unchanged if no mapping"
        return self.externalToInternal.get(externalName, externalName)

    def __str__(self):
        return "intToExt={} extToInt={}".format(self.internalToExternal, self.externalToInternal)


class SymEnumMeta(EnumMeta):
    """metaclass for SysEnumMeta that implements looking up of singleton members
    by string name."""

    @staticmethod
    def _symEnumValueUpdate(classdict, name, externalNameMap):
        """record info about a member specified with SymEnum and update value in classdict
        to be actual value rather than SymEnumValue"""
        symValue = classdict[name]
        if six.PY3:
            # under python3, enum does some sanity check, must remove from _EnumDict before
            # reinserting
            del classdict._member_names[classdict._member_names.index(name)]
            del classdict[name]
        classdict[name] = symValue.value
        externalNameMap.add(name, symValue.externalName)

    @staticmethod
    def _buildExternalNameMap(classdict):
        externalNameMap = classdict["__externalNameMap__"] = _SysEnumExternalNameMap()
        for name in list(classdict.keys()):
            if isinstance(classdict[name], SymEnumValue):
                SymEnumMeta._symEnumValueUpdate(classdict, name, externalNameMap)

    def __new__(metacls, cls, bases, classdict):
        "updates class fields defined as SymEnumValue to register external names"
        if SymEnum in bases:
            SymEnumMeta._buildExternalNameMap(classdict)
        return EnumMeta.__new__(metacls, cls, bases, classdict)

    @staticmethod
    def _lookUpByStr(cls, value):
        if six.PY2 and isinstance(value, six.text_type):
            value = value.decode()  # force unicode to str for field names

        # map string name to instance, check for external name
        member = cls._member_map_.get(cls.__externalNameMap__.toInternalName(value))
        if member is None:
            member = cls._member_map_.get(cls.__externalNameMap__.toExternalName(value))
        if member is None:
            raise ValueError("'{}' is not a member, external name, or alias of {}".format(value, cls.__name__))
        else:
            return member

    def __call__(cls, value, names=None, module=None, typ=None):
        "look up a value object, either by name of value,"
        if (names is None) and isinstance(value, six.string_types):
            return SymEnumMeta._lookUpByStr(cls, value)
        else:
            return EnumMeta.__call__(cls, value, names, module=module, type=typ)


@total_ordering
class SymEnumMixin(object):
    """Mixin that adds comparisons for SymEnum"""

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, SymEnum):
            return self.value == other.value
        else:
            return self.value == other

    def __lt__(self, other):
        if isinstance(other, SymEnum):
            return self.value < other.value
        else:
            return self.value < other

    def __reduce_ex__(self, proto):
        return self.__class__, ()


class SymEnum(six.with_metaclass(SymEnumMeta, SymEnumMixin, Enum)):
    """
    Metaclass for symbolic enumerations.  These are easily converted between
    string values and Enum objects.  This support construction from string
    values and str() returns value without class name.  Aliases can be
    added using the Enum approach of:
        name = 1
        namealias = val

    To handle string values that are not valid Python member names, an external
    name maybe associated with a field using a SymEnumValue object
        utr5 = SymEnumValue(1, "5'UTR")

    Either field name or external name maybe used to obtain a value.  The external
    name is returned with str().

    Instances of the enumerations are obtained by either string name or int
    value:
       SymEnum(strName)
       SymEnum(intVal)
    """

    def __str__(self):
        return self.__externalNameMap__.toExternalName(self.name)


__all__ = (SymEnumValue.__name__, SymEnum.__name__)
