import unittest, sys, string
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.Enumeration import Enumeration
from pycbio.sys.TestCaseBase import TestCaseBase

class EnumerationTests(TestCaseBase):

    def testBasics(self):
        Colors = Enumeration("Colors", ["red", "green", "blue"])
        self.failUnlessEqual(Colors.red.name, "red")
        self.failUnlessEqual(Colors.green.name, "green")
        self.failUnlessEqual(Colors.blue.name, "blue")
        self.failUnless(Colors.red < Colors.blue)
        self.failUnless(Colors.red == Colors.red)
        self.failUnless(Colors.red != Colors.blue)
        self.failUnless(Colors.red != None)
        self.failUnless(None != Colors.red)

    def testLookup(self):
        Colors = Enumeration("Colors", ["red", "green", "blue"])
        self.failUnless(Colors.red == Colors.lookup("red"))
        self.failUnless(Colors.green == Colors.lookup("green"))
        self.failUnless(Colors.green != Colors.lookup("red"))

    def testAliases(self):
        Name = Enumeration("Name", ["Fred",  ("Rick", "Richard", ("Dick", "HeyYou")), ("Bill", "Willian")])
        self.failUnlessEqual(Name.lookup("Richard"), Name.Rick)
        self.failUnless(Name.lookup("Richard") is Name.Rick)
        self.failUnlessEqual(Name.lookup("Dick"), Name.Rick)
        self.failUnless(Name.lookup("Dick") is Name.Rick)
        self.failUnless(Name.lookup("Rick") == Name.Rick)
        self.failUnless(Name.lookup("HeyYou") == Name.Rick)
        self.failUnless(Name.lookup("Fred") == Name.Fred)
        self.failUnless(Name.lookup("Fred") is Name.Fred)
        self.failUnless(str(Name.Rick) == "Richard")

    def testAliasesBug1(self):
        "forgot comma in one-element tuple, assert catches this problem"
        try:
            Stat = Enumeration("Stat",
                               ["okay",
                                ("notConserved","notConserved", ("no_alignment")),
                                "bad_3_splice", "bad_5_splice"])
            if __debug__:
                self.fail("should have asserted")
        except AssertionError:
            pass
        
    def testBitSetValues(self):
        Stat = Enumeration("Stat",
                           ["okay",
                            ("notConserved","notConserved", ("no_alignment",)),
                            "bad_3_splice", "bad_5_splice"],
                           bitSetValues=True)
        self.failUnlessEqual(Stat.okay, 1)
        self.failUnlessEqual(Stat.notConserved, 2)
        self.failUnlessEqual(Stat.bad_5_splice, 8)
        self.failUnlessEqual(int(Stat.bad_5_splice), 8)
        self.failUnlessEqual(Stat.maxNumValue, 8)
        vals = Stat.getValues(9)
        self.failUnlessEqual(len(vals), 2)
        self.failUnless(vals[0] is Stat.okay)
        self.failUnless(vals[1] is Stat.bad_5_splice)

    def testSetOps(self):
        Colors = Enumeration("Colors", ["red", "green", "blue"])
        colSet = set([Colors.blue, Colors.green])
        self.failUnless(Colors.green in colSet)
        self.failIf(Colors.red in colSet)

    def testErrors(self):
        Colors = Enumeration("Colors", ["red", "green", "blue"])
        # check if immutable
        try:
            Colors.red.name = "purple"
            self.fail("immutable object modified")
        except TypeError:
            pass
        try:
            Colors.red = None
            self.fail("immutable object modified")
        except TypeError:
            pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(EnumerationTests))
    return suite

if __name__ == '__main__':
    unittest.main()
