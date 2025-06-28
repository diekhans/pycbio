# Copyright 2006-2025 Mark Diekhans
import sys
from collections import namedtuple
from pytest import approx
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


class Point(namedtuple('point', ('x', 'y'))):
    @typeOps.cached_immutable_property
    def norm(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __del__(self):
        typeOps.cached_immutable_property_free(self)

def testNameTupleMemoize():
    # checks internals
    pt = Point(10, 20)
    ptid = id(pt)
    assert ptid not in typeOps._memo_cache
    n = pt.norm
    assert ptid in typeOps._memo_cache
    assert n == approx(22.36068, rel=1e-5)
    # check if memo gets released
    del pt
    assert ptid not in typeOps._memo_cache
