# Copyright 2006-2012 Mark Diekhans
"array and matrix classed, indexed by Enumerations"

from pycbio.sys.enumeration import Enumeration


class EnumArray(list):
    """array indexed by an Enumeration."""

    def __init__(self, enum, initVal=None):
        for i in range(enum.maxNumValue + 1):
            self.append(initVal)

    def __getitem__(self, eVal):
        return super(EnumArray, self).__getitem__(eVal.numValue)

    def __setitem__(self, eVal, val):
        return super(EnumArray, self).__setitem__(eVal.numValue, val)


class EnumMatrix(EnumArray):
    """matrix indexed by Enumerations."""

    def __init__(self, rowEnum, colEnum, initVal=None):
        assert(isinstance(rowEnum, Enumeration))
        assert(isinstance(colEnum, Enumeration))
        super(EnumMatrix, self).__init__(rowEnum)
        self.rowEnum = rowEnum
        self.colEnum = colEnum
        for val in self.rowEnum.values:
            self[val] = EnumArray(self.colEnum, initVal)
