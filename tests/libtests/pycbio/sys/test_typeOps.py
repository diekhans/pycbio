# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys import typeOps

# FIXME: many more tests needed


def testAnnon():
    ao = typeOps.annon(a=10, b=20, fred="spaced out")
    assert ao.a == 10
    assert ao.b == 20
    assert str(ao) == "a=10, b=20, fred='spaced out'"

def testAttrdict():
    class ODict:
        def __init__(self):
            self.f = 100

    class OSlots:
        __slots__ = ("f")

        def __init__(self):
            self.f = 101

    odict = ODict()
    assert typeOps.attrdict(odict)['f'] == 100
    oslots = OSlots()
    assert typeOps.attrdict(oslots)['f'] == 101
