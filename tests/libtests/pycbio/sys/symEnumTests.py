# Copyright 2006-2014 Mark Diekhans
import unittest
import sys
import cPickle
if __name__ == '__main__':
    sys.path.append("../../../../lib")
from pycbio.sys.symEnum import SymEnum, SymEnumValue
from pycbio.sys.testCaseBase import TestCaseBase


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

class SymEnumTests(TestCaseBase):
    def testBasics(self):
        self.assertEqual(Color.red.name, "red")
        self.assertEqual(Color.green.name, "green")
        self.assertEqual(Color.blue.name, "blue")
        self.assertTrue(Color.red < Color.blue)
        self.assertTrue(Color.red == Color.red)
        self.assertTrue(Color.red != Color.blue)
        self.assertTrue(Color.red is not None)
        self.assertTrue(None != Color.red)  # flake8: noqa

    def testLookup(self):
        self.assertTrue(Color.red == Color("red"))
        self.assertTrue(Color.green == Color("green"))
        self.assertTrue(Color.green != Color("red"))

    def testStrings(self):
        self.assertTrue(str(Color.red) == "red")
        self.assertTrue(str(Color.green) == "green")
        self.assertTrue(sorted([str(c) for c in Color]), ["red", "green", "blue"])

    def testAliases(self):
        class Name(SymEnum):
            Fred = 1
            Rick = 2
            Richard = Dick = HeyYou = Rick
            Bill = 3
        self.assertTrue(Name("Richard") is Name.Rick)
        self.assertEqual(Name("Dick"), Name.Rick)
        self.assertTrue(Name("Dick") is Name.Rick)
        self.assertTrue(Name("Rick") == Name.Rick)
        self.assertTrue(Name("HeyYou") == Name.Rick)
        self.assertTrue(Name("Fred") == Name.Fred)
        self.assertTrue(Name("Fred") is Name.Fred)
        self.assertEqual([n for n in Name], [Name.Fred, Name.Rick, Name.Bill])

    def testSetOps(self):
        colSet = set([Color.blue, Color.green])
        self.assertTrue(Color.green in colSet)
        self.assertFalse(Color.red in colSet)

    def testNumberDef(self):
        class NumDef(SymEnum):
            neg = -2
            zero = 0
            pos = 2
            big = 3
        values = [(v.name, v.value) for v in NumDef]
        self.assertEqual(values, [('neg', -2), ('zero', 0), ('pos', 2), ('big', 3)])
        self.assertEqual(NumDef(2), NumDef.pos)

    def __testColorPickleProtocol(self, protocol):
        stuff = {Color.red: "red one",
                 Color.green: "green one"}

        world = cPickle.dumps((Color, stuff,), protocol)
        color, stuff2 = cPickle.loads(world)

        self.assertTrue(Color.red in stuff2)
        self.assertTrue(Color.green in stuff2)

    def testColorPickle2(self):
        self.assertTrue(cPickle.HIGHEST_PROTOCOL == 2)
        self.__testColorPickleProtocol(2)

    def testColorPickle1(self):
        self.__testColorPickleProtocol(1)

    def testColorPickle0(self):
        self.__testColorPickleProtocol(0)

    def testExtNameLookup(self):
        self.assertEqual(GeneFeature.promoter, GeneFeature("promoter"))
        self.assertEqual(GeneFeature.utr5, GeneFeature("5'UTR"))
        self.assertEqual(GeneFeature.utr5, GeneFeature("utr5"))
        self.assertEqual(GeneFeature.cds, GeneFeature("CDS"))
        self.assertEqual(GeneFeature.utr3, GeneFeature("3'UTR"))
        self.assertEqual(GeneFeature.utr3, GeneFeature("utr3"))
        self.assertEqual(GeneFeature.cds, GeneFeature("coding"))

    def testExtNameStrings(self):
        self.assertEqual(str(GeneFeature.promoter), "promoter")
        self.assertEqual(str(GeneFeature.utr5), "5'UTR")
        self.assertEqual(str(GeneFeature.cds), "CDS")
        self.assertEqual(str(GeneFeature.utr3), "3'UTR")
        self.assertNotEqual(str(GeneFeature.utr3), "utr3")
        self.assertEqual(str(GeneFeature.coding), "CDS")
        self.assertEqual(sorted([str(c) for c in GeneFeature]), ["3'UTR", "5'UTR", "CDS", "promoter"])

    def __testGeneFeaturePickleProtocol(self, protocol):
        stuff = {GeneFeature.utr3: "UTR'3 one",
                 GeneFeature.cds: "CDS one"}
        world = cPickle.dumps((GeneFeature, stuff,), protocol)
        geneFeature, stuff2 = cPickle.loads(world)

        self.assertTrue(GeneFeature.utr3 in stuff2)
        self.assertTrue(GeneFeature.cds in stuff2)

    def testGeneFeaturePickle2(self):
        self.assertTrue(cPickle.HIGHEST_PROTOCOL == 2)
        self.__testGeneFeaturePickleProtocol(2)
    def testGeneFeaturePickle1(self):
        self.__testGeneFeaturePickleProtocol(1)
    def testGeneFeaturePickle0(self):
        self.__testGeneFeaturePickleProtocol(0)

    def testBasicsFn(self):
        FnColor = SymEnum("FnColor", ("red","green", "blue"))
        self.assertEqual(FnColor.red.name, "red")
        self.assertEqual(FnColor.green.name, "green")
        self.assertEqual(FnColor.blue.name, "blue")
        self.assertTrue(FnColor.red < FnColor.blue)
        self.assertTrue(FnColor.red == FnColor.red)
        self.assertTrue(FnColor.red != FnColor.blue)
        self.assertTrue(FnColor.red is not None)
        self.assertTrue(None != FnColor.red)

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(SymEnumTests))
    return ts

if __name__ == '__main__':
    unittest.main()
