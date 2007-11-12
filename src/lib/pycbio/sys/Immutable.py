
# FIXME: __new__ maybe helpful in defining immutables, should at least use a slot,
# count redefine rather then override __setattr__, __delattr__

class Immutable(object):
    """Base class to make an object instance immutable.  Call makeImmutable
    after construction"""
    
    def makeImmutable(self):
        self.immutable = True

    def __setattr__(self, attr, value):
        if self.__dict__.has_key("immutable"):
            raise TypeError("Immutable object", self)
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        if self.__dict__.has_key("immutable"):
            raise TypeError("Immutable object", self)
        object.__delattr__(self, attr)

