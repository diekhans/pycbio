# Copyright 2006-2025 Mark Diekhans
import sys
import pickle
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.symEnum import SymEnum, SymEnumValue, auto

class Color(SymEnum):
    red = 1
    green = 2
    blue = 3


class GeneFeature(SymEnum):
    promoter = 1
    utr5 = SymEnumValue(2, "5'UTR")
    cds = SymEnumValue(3, "CDS")
    utr3 = SymEnumValue(4, "3'UTR")
    coding = cds

class ColorNoDict(SymEnum):
    "however __slots__ doesn't seem to do anything, there is still a dict"
    __slots__ = ()
    purple = 1
    gold = 2
    black = 3


def _checkColor(colorCls):
    # this useful for pickle tests
    assert colorCls.red.name == "red"
    assert colorCls.green.name == "green"
    assert colorCls.blue.name == "blue"
    assert colorCls.red < colorCls.blue
    assert colorCls.red == colorCls.red
    assert colorCls.red != colorCls.blue
    assert colorCls.red is not None
    assert None != colorCls.red   # noqa

def testBasics():
    _checkColor(Color)

def testLookup():
    assert Color.red == Color("red")
    assert Color.green == Color("green")
    assert Color.green != Color("red")

def testStrings():
    assert str(Color.red == "red")
    assert str(Color.green == "green")
    assert sorted([str(c) for c in Color]) == ["blue", "green", "red"]

def testAliases():
    class Name(SymEnum):
        Fred = 1
        Rick = 2
        Richard = Dick = HeyYou = Rick
        Bill = 3
    assert Name("Richard") is Name.Rick
    assert Name("Dick") == Name.Rick
    assert Name("Dick") is Name.Rick
    assert Name("Rick") == Name.Rick
    assert Name("HeyYou") == Name.Rick
    assert Name("Fred") == Name.Fred
    assert Name("Fred") is Name.Fred
    assert [n for n in Name] == [Name.Fred, Name.Rick, Name.Bill]

def testAliasesStrValue():
    # alias should not be returned for string name
    class Name(SymEnum):
        Fred = 1
        Rick = 2
        Arther = Rick
    assert str(Name.Arther) == "Rick"
    assert str(Name.Rick) == "Rick"

def testSetOps():
    colSet = set([Color.blue, Color.green])
    assert Color.green in colSet
    assert Color.red not in colSet

def testNumberDef():
    class NumDef(SymEnum):
        neg = -2
        zero = 0
        pos = 2
        big = 3
    values = [(v.name, v.value) for v in NumDef]
    assert values == [('neg', -2), ('zero', 0), ('pos', 2), ('big', 3)]
    assert NumDef(2) == NumDef.pos

def _testColorPickleProtocol(protocol):
    stuff = {Color.red: "red one",
             Color.green: "green one"}

    world = pickle.dumps((Color, stuff,), protocol)
    color, stuff2 = pickle.loads(world)

    assert Color.red in stuff2
    assert Color.green in stuff2

def testColorPickle():
    for protocol in range(0, pickle.HIGHEST_PROTOCOL + 1):
        _testColorPickleProtocol(protocol)

def testExtNameLookup():
    assert GeneFeature.promoter == GeneFeature("promoter")
    assert GeneFeature.utr5 == GeneFeature("5'UTR")
    assert GeneFeature.utr5 == GeneFeature("utr5")
    assert GeneFeature.cds == GeneFeature("CDS")
    assert GeneFeature.utr3 == GeneFeature("3'UTR")
    assert GeneFeature.utr3 == GeneFeature("utr3")
    assert GeneFeature.cds == GeneFeature("coding")

def testExtNameStrings():
    assert str(GeneFeature.promoter) == "promoter"
    assert str(GeneFeature.utr5) == "5'UTR"
    assert str(GeneFeature.cds) == "CDS"
    assert str(GeneFeature.utr3) == "3'UTR"
    assert str(GeneFeature.coding) == "CDS"
    assert sorted([str(c) for c in GeneFeature]) == ["3'UTR", "5'UTR", "CDS", "promoter"]

def _geneFeaturePickleProtocolTest(protocol):
    stuff = {GeneFeature.utr3: "UTR'3 one",
             GeneFeature.cds: "CDS one"}
    world = pickle.dumps((GeneFeature, stuff,), protocol)
    geneFeature, stuff2 = pickle.loads(world)

    assert GeneFeature.utr3 in stuff2
    assert GeneFeature.cds in stuff2

def testGeneFeaturePickle():
    for protocol in range(0, pickle.HIGHEST_PROTOCOL + 1):
        _geneFeaturePickleProtocolTest(protocol)

def testBasicsFn():
    FnColor = SymEnum("FnColor", ("red", "green", "blue"))
    assert FnColor.red.name == "red"
    assert FnColor.green.name == "green"
    assert FnColor.blue.name == "blue"
    assert FnColor.red < FnColor.blue
    assert FnColor.red == FnColor.red
    assert FnColor.red != FnColor.blue
    assert FnColor.red is not None
    assert None != FnColor.red   # noqa

def testAutoDef():
    class AutoDef(SymEnum):
        first = auto()
        second = auto()
        third = auto()
    assert [('first', 1), ('second', 2), ('third', 3)] == list(sorted([(str(v), v.value) for v in AutoDef]))

def testWithSymEnumValue():
    class CdsStat(SymEnum):
        none = SymEnumValue("none", "none")
        unknown = SymEnumValue("unknown", "unk")
        incomplete = SymEnumValue("incomplete", "incmpl")
        complete = SymEnumValue("complete", "cmpl")

    assert str(CdsStat("incomplete")) == "incmpl"
    assert str(CdsStat("incmpl")) == "incmpl"
    assert str(CdsStat(u"incmpl")) == "incmpl"

def testBasicsNoDict():
    assert ColorNoDict.purple.name == "purple"
    assert ColorNoDict.gold.name == "gold"
    assert ColorNoDict.black.name == "black"
    assert ColorNoDict.purple < ColorNoDict.black
    assert ColorNoDict.purple == ColorNoDict.purple
    assert ColorNoDict.purple != ColorNoDict.black
    assert ColorNoDict.purple is not None
    assert None != ColorNoDict.purple  # noqa

def testLookupNoDict():
    assert ColorNoDict.purple == ColorNoDict("purple")
    assert ColorNoDict.gold == ColorNoDict("gold")
    assert ColorNoDict.gold != ColorNoDict("purple")

def testStringsNoDict():
    assert str(ColorNoDict.purple == "purple")
    assert str(ColorNoDict.gold == "gold")
    assert sorted([str(c) for c in ColorNoDict]) == ['black', 'gold', 'purple']

def testSelfConvert():
    assert Color(Color.red) is Color.red

def testFormat():
    assert "{}".format(Color.red) == "red"

def testFormatPad():
    assert "{:5}x".format(Color.red) == "red  x"

def _pickleProtocolTest(prot):
    stuff = {}
    stuff[Color.red] = "red one"
    stuff[Color.green] = "green one"
    world = pickle.dumps((Color, stuff), prot)
    Color2, stuff2 = pickle.loads(world)

    assert Color2.red in stuff2
    assert Color2.green in stuff2
    _checkColor(Color2)

def testPickle():
    for prot in range(0, pickle.HIGHEST_PROTOCOL + 1):
        _pickleProtocolTest(prot)

def testCall():
    # this goes thought Enum.__new__ like pickle, and broken SymEnum in 3.12
    c = Color(1)
    assert c.red == Color.red
