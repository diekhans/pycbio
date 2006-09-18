import unittest, sys, string
if __name__ == '__main__':
    sys.path.append("../../..")
from pycbio.tsv.TSVTable import TSVTable
from pycbio.tsv.TSVError import TSVError
from pycbio.sys.TestCaseBase import TestCaseBase
from pycbio.hgdata.AutoSql import intArrayType

class ReadTests(TestCaseBase):
    def testLoad(self):
        tsv = TSVTable(self.getInputFile("mrna1.tsv"))
        self.failUnlessEqual(len(tsv), 10)
        for r in tsv:
            self.failUnlessEqual(len(r), 22)
        r = tsv[0]
        self.failUnlessEqual(r["qName"], "BC032353")
        self.failUnlessEqual(r[10],"BC032353")
        self.failUnlessEqual(r.qName, "BC032353")

    def testMultiIdx(self):
        tsv = TSVTable(self.getInputFile("mrna1.tsv"), multiKeyCols=("tName", "tStart"))
        rows = tsv.idx.tName["chr1"]
        self.failUnlessEqual(len(rows), 10)
        self.failUnlessEqual(rows[1].qName, "AK095183")

        rows = tsv.idx.tStart["4268"]
        self.failUnlessEqual(len(rows), 5)
        self.failUnlessEqual(rows[0].qName, "BC015400")

    def testColType(self):
        def onOffParse(str):
            if str == "on":
                return True
            elif str == "off":
                return False
            else:
                raise ValueError("invalid onOff value: " + str)
            
        def onOffFmt(val):
            if type(val) != bool:
                raise TypeError("onOff value not a bool: " + str(type(val)))
            if val:
                return "on"
            else:
                return "off"
            
        typeMap = {"intCol": int, "floatCol": float, "onOffCol": (onOffParse, onOffFmt)}

        tsv = TSVTable(self.getInputFile("types.tsv"), typeMap=typeMap)

        r = tsv[0]
        self.failUnlessEqual(r.strCol, "name1")
        self.failUnlessEqual(r.intCol, 10)
        self.failUnlessEqual(r.floatCol, 10.01)
        self.failUnlessEqual(str(r), "name1\t10\t10.01\ton")

        r = tsv[2]
        self.failUnlessEqual(r.strCol, "name3")
        self.failUnlessEqual(r.intCol, 30)
        self.failUnlessEqual(r.floatCol, 30.555)
        self.failUnlessEqual(str(r), "name3\t30\t30.555\toff")

    def testColTypeDefault(self):
        # default to int type
        typeMap = {"strand": str, "qName": str, "tName": str,
                   "blockSizes": intArrayType,
                   "qStarts": intArrayType, "tStarts": intArrayType}
        
        tsv = TSVTable(self.getInputFile("mrna1.tsv"), uniqKeyCols="qName",
                  typeMap=typeMap, defaultColType=int)
        r = tsv.idx.qName["AK095183"]
        self.failUnlessEqual(r.tStart, 4222)
 	self.failUnlessEqual(r.tEnd, 19206)
        self.failUnlessEqual(r.tName, "chr1")
        self.failUnlessEqual(r.tStart, 4222)

        tStarts = (4222,4832,5658,5766,6469,6719,7095,7355,7777,8130,14600,19183)
        self.failUnlessEqual(len(r.tStarts), len(tStarts))
        for i in xrange(len(tStarts)):
            self.failUnlessEqual(r.tStarts[i], tStarts[i])

    def testMissingIdxCol(self):
        err = None
        try:
            tsv = TSVTable(self.getInputFile("mrna1.tsv"), multiKeyCols=("noCol",))
        except TSVError,e:
            err = e
        self.failIfEqual(err, None)

    def testWrite(self):
        tsv = TSVTable(self.getInputFile("mrna1.tsv"), uniqKeyCols="qName")
        fh = open(self.getOutputFile(".tsv"), "w")
        tsv.write(fh)
        fh.close()
        self.diffExpected(".tsv")

    def testAddColumn(self):
        tsv = TSVTable(self.getInputFile("mrna1.tsv"), uniqKeyCols="qName")
        tsv.addColumn("joke")
        i = 0
        for row in tsv:
            row.joke = i
            i += 1
        fh = open(self.getOutputFile(".tsv"), "w")
        tsv.write(fh)
        fh.close()
        self.diffExpected(".tsv")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ReadTests))
    return suite

if __name__ == '__main__':
    unittest.main()
