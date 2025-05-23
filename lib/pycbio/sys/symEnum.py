# Copyright 2006-2025 Mark Diekhans
import sys
from enum import Enum, EnumMeta, _EnumDict, auto
from functools import total_ordering

# FIXME: this is a complex relationship with Enum
# see issues.org

# EnumType (aka EnumMeta) has
#    def __call__(cls, value, names=_not_given, ...)
# which turns around and modify value before call __new__ if not set.
# This was added somewhere in 12.x line, this compatibility with older version.
try:
    from enum import _not_given
except ImportError:
    _not_given = None

SymEnum = None  # class defined after use


class SymEnumValue:
    "Class used to define SymEnum member that have additional attributes."
    __slots__ = ("value", "externalName")

    def __init__(self, value, externalName=None):
        self.value = value
        self.externalName = externalName

    def __repr__(self):
        return f'SymEnumValue({self.value}, {self.externalName})'

class _SysEnumExternalNameMap:
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
        return f"intToExt={self.internalToExternal} extToInt={self.externalToInternal}"

class _SymEnumDict(_EnumDict):
    """Extends _EnumDict to record internal/external name mapping.
    This must be done as a wrapper around _EnumDict instead of
    as an external edit, as _EnumDict.__setitem__ does the auto()
    assignment. This converts SymEnumValue(auto(), "ext") to
    just the auto() value.
    """
    __slots__ = ("externalNameMap")

    def __init__(self):
        super().__init__()
        self.externalNameMap = _SysEnumExternalNameMap()

    def __setitem__(self, key, value):
        if isinstance(value, SymEnumValue):
            if value.externalName is not None:
                self.externalNameMap.add(key, value.externalName)
            value = value.value
        super().__setitem__(key, value)

    def toExternalName(self, internalName):
        "return name unchanged if no mapping"
        return self.internalToExternal.get(internalName, internalName)

    def toInternalName(self, externalName):
        "return name unchanged if no mapping"
        return self.externalToInternal.get(externalName, externalName)


class SymEnumMeta(EnumMeta):
    """metaclass for SysEnumMeta that implements looking up of singleton members
    by string name."""

    @classmethod
    def __prepare__(metacls, cls, bases, **kwds):
        # WARNING: this is copied from EnumType (aka EnumMeta) in standard
        # enum.py to use _SymEnumDict and replaces the EnumType

        # check that previous enum members do not exist
        # not in 3.7, name changed in 3.11
        if hasattr(metacls, "_check_for_existing_members"):
            metacls._check_for_existing_members(cls, bases)  # 3.9
        elif hasattr(metacls, "_check_for_existing_members_"):
            metacls._check_for_existing_members_(cls, bases)  # 3.11
        # create the namespace dict
        enum_dict = _SymEnumDict()
        enum_dict._cls_name = cls
        # inherit previous flags and _generate_next_value_ function
        if sys.version_info.minor <= 7:
            member_type, first_enum = metacls._get_mixins_(bases)
        else:
            member_type, first_enum = metacls._get_mixins_(cls, bases)
        if first_enum is not None:
            enum_dict['_generate_next_value_'] = getattr(
                first_enum, '_generate_next_value_', None,
            )
        return enum_dict

    def __new__(metacls, clsname, bases, classdict, *, boundary=None, _simple=False, **kwds):
        "store away externalNameMap from _SymEnumDict"
        # from enum.py: all enum instances are actually created during class construction
        # without calling this method; this method is called by the metaclass'
        # __call__ (i.e. Color(3) ), and by pickle

        if SymEnum in bases:
            classdict["__externalNameMap__"] = classdict.externalNameMap
        # keyword arguments added in 3.10, boundary and _simple in 3.11, which get added to **kwds
        if sys.version_info.minor <= 10:
            return super(SymEnumMeta, metacls).__new__(metacls, clsname, bases, classdict)
        else:
            return super(SymEnumMeta, metacls).__new__(metacls, clsname, bases, classdict, boundary=boundary, _simple=_simple, **kwds)

    @staticmethod
    def _lookUpByStr(cls, value):
        # map string name to instance, check for external name
        member = cls._member_map_.get(cls.__externalNameMap__.toInternalName(value))
        if member is None:
            member = cls._member_map_.get(cls.__externalNameMap__.toExternalName(value))
        if member is None:
            raise ValueError("'{}' is not a member, external name, or alias of {}".format(value, cls.__name__))
        else:
            return member

    def __call__(cls, value, names=_not_given, module=None, typ=None):
        "look up a value object, either by name or value"
        if (names is _not_given) and isinstance(value, str):
            return SymEnumMeta._lookUpByStr(cls, value)
        else:
            return EnumMeta.__call__(cls, value, names, module=module, type=typ)


@total_ordering
class SymEnumMixin:
    """Mixin that adds comparisons and other functions for SymEnum"""

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
        return self.__class__, (self.value, )


class SymEnum(SymEnumMixin, Enum, metaclass=SymEnumMeta):  # noqa: F811
    """Class for symbolic enumerations. The field name is normally the
    symbolic value. These can be converted between string values and SymEnum
    objects.  This supports construction from string values and str() returns
    the value without the class name.

    This is useful for storing and parsing enums in files or databases as
    strings and using enums as command-line argument values.

    For example:

        >>> class Color(SymEnum):
        ...     purple = 1
        ...     gold = 2
        ...     black = 3

        >>> Color("gold")
        <Color.gold: 2>
        >>> str(Color.purple)
        'purple'
        >>> Color(3)
        <Color.black: 3>

    Aliases can be added using the Enum approach:

        >>> class DarkColor(SymEnum):
        ...     gray = 1
        ...     grey = 1  # alias for gray
        ...     black = 2
        ...     goth = 2  # alias for black

        >>> str(DarkColor.goth)
        'black'
        >>> DarkColor("grey")
        <DarkColor.gray: 1>

    A member can be looked up by alias name, but the main string name is
    returned when accessed.

    The functional API works as with Enum, and the auto() method of field
    initialization may be used instead of integer constants.

    To handle string values that are not valid Python member names, an
    external name can be associated with a field using a SymEnumValue object:

        >>> class GeneFeature(SymEnum):
        ...     promoter = 1
        ...     utr5 = SymEnumValue(2, "5'UTR")
        ...     cds = SymEnumValue(3, "CDS")
        ...     utr3 = SymEnumValue(4, "3'UTR")
        ...     coding = cds

        >>> str(GeneFeature.utr5)
        "5'UTR"
        >>> GeneFeature("5'UTR")
        <GeneFeature.utr5: 2>

    Instances of a SymEnum are obtained by either string name or int value:

        >>> Color("gold")
        <Color.gold: 2>
        >>> Color(2)
        <Color.gold: 2>

    To use as an argument type in argparse:
        type=Color, choices=Color

    """
    def __str__(self):
        return self.__externalNameMap__.toExternalName(self.name)

    def __format__(self, fmtspec):
        return format(str(self), fmtspec)


__all__ = (SymEnumValue.__name__, SymEnum.__name__, auto.__name__)
