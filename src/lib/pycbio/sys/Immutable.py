"""
Base class used to define immutable objects
"""

class Immutable(object):
    """Base class to make an object instance immutable.  Call 
    Immutable.__init__(self) after construction to make immutable"""

    __immAttr = "_Immutable__immutable"
    __slots__ = (__immAttr,)

    def __new__(cls, *args, **kvs):
        self = object.__new__(cls)
        object.__setattr__(self, Immutable.__immAttr, False)
        return self

    def __init__(self):
        "makes derived objects immutable"
        object.__setattr__(self, Immutable.__immAttr, True)

    def __setattr__(self, attr, value):
        if self.__immutable:
            raise TypeError("immutable object", self)
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        if self.__immutable:
            raise TypeError("immutable object", self)
        object.__delattr__(self, attr)

