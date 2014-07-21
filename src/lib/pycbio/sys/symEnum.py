# Copyright 2006-2014 Mark Diekhans

from enum import Enum,EnumMeta

class SymEnumMeta(EnumMeta):
    """metaclass for SysEnumMeta that implements looking up singleton members
    by string name."""

    def __call__(cls, value, names=None, module=None, type=None):
        "look up a value object, either by name of value,"
        if (names is None) and isinstance(value, str):
            # map string name to instance
            member = cls._member_map_.get(value)
            if member == None:
                raise ValueError("'%s' is not a member or alias of %s" % (value, cls.__name__))
            else:
                return member
        else:
            return EnumMeta.__call__(cls, value, names, module, type)



class SymEnum(Enum):
    """
    Metaclass for symbolic enumerations.  These are easily converted between
    string values and Enum objects.  This support construction from string
    values and str() returns value without class name.  Aliases can be
    added using the Enum approach of:
        val = 1
        valalias = val
    """
    __metaclass__ = SymEnumMeta

    def __str__(self):
        return self.name

    def __le__(self, other):
        if isinstance(other, SymEnum):
            return self.value <= other.value
        else:
            return self.value <= other

    def __lt__(self, other):
        if isinstance(other, SymEnum):
            return self.value < other.value
        else:
            return self.value < other

    def __ge__(self, other):
        if isinstance(other, SymEnum):
            return self.value >= other.value
        else:
            return self.value >= other

    def __gt__(self, other):
        if isinstance(other, SymEnum):
            return self.value > other.value
        else:
            return self.value > other

    def __eq__(self, other):
        if isinstance(other, SymEnum):
            return self.value == other.value
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, SymEnum):
            return self.value != other.value
        else:
            return True
