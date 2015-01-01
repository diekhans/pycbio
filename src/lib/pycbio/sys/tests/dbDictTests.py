# Copyright 2006-2012 Mark Diekhans
import unittest, sys
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.sys.dbDict import DbDict
from pycbio.sys.testCaseBase import TestCaseBase

class DbDictTests(TestCaseBase):

    def __assertKeyValues(self, dbd, expect):
        "gets sort tuple of (key values) and compare"
        keyValues = [(k, dbd[k]) for k in dbd.keys()]
        keyValues.sort(key=lambda kv: kv[0])
        keyValues = tuple(keyValues)
        self.assertEqual(keyValues, expect)

    def testBasic(self):
        dbfile = self.getOutputFile("basic.sqlite")
        dbd = DbDict(dbfile)
        dbd["one"] = "value 1" 
        dbd["two"] = "value 2" 
        dbd["three"] = "value 3" 
        keys = dbd.keys()
        keys.sort()
        self.__assertKeyValues(dbd, (('one', 'value 1'), ('three', 'value 3'), ('two', 'value 2')))

        dbd["two"] = "value 2.1" 
        self.__assertKeyValues(dbd, (('one', 'value 1'), ('three', 'value 3'), ('two', 'value 2.1')))

        del dbd["two"]
        self.__assertKeyValues(dbd, (('one', 'value 1'), ('three', 'value 3')))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(DbDict))
    return ts

if __name__ == '__main__':
    unittest.main()
