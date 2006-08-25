from pycbio.sys import fileOps
import os.path, sys, unittest, difflib

class TestCaseBase(unittest.TestCase):
    """Base class for test case with various test support functions"""

    def getId(self):
        """get the fixed test id, which is in the form moduleBase.class.method
        which avoids different ids when test module is run as main or
        from a larger program"""
        # last two parts are class and method
        idParts = self.id().split(".")[-2:]
        
        # module name is __main__ when run standalone, so get base file name
        mod = os.path.splitext(os.path.basename(sys.modules[self.__class__.__module__].__file__))[0]
        ftid = mod + "." + str.join(".",idParts)
        return ftid

    def getTestDir(self):
        """find test directory, where concrete class is defined."""
        testDir =  os.path.dirname(sys.modules[self.__class__.__module__].__file__)
        if testDir == "":
            testDir = "."
        return testDir

    def getInputFile(self, fname):
        """Get a path to a file in the test input directory"""
        return self.getTestDir() + "/input/" + fname

    def getOutputDir(self):
        """get the path to the output directory to use for this test, create if it doesn't exist"""
        d = self.getTestDir() + "/output";
        fileOps.ensureDir(d)
        return d

    def getOutputFile(self, ext):
        """Get path to the output file, using the current test id and append
        ext, which should contain a dot"""
        f = self.getOutputDir() + "/" + self.getId() + ext;
        fileOps.ensureFileDir(f)
        return f

    def getExpectedFile(self, ext):
        """Get path to the expected file, using the current test id and append ext"""
        return self.getTestDir() + "/expected/" + self.getId() + ext;

    def _getLines(self, file):
        fh = open(file)
        lines = fh.readlines()
        fh.close()
        return lines

    def mustExist(self, path):
        if not os.path.exists(path):
            self.fail("file does not exist: " + path)

    def diffExpected(self, ext):
        """diff expected and output files"""

        expFile = self.getExpectedFile(ext)
        expLines = self._getLines(expFile)

        outFile = self.getOutputFile(ext)
        outLines = self._getLines(outFile)

        diff = difflib.unified_diff(expLines, outLines, expFile, outFile)
        cnt = 0
        for l in diff:
            print l,
            cnt += 1
        self.failUnless(cnt == 0)
            

    def createOutputFile(self, ext, contents=""):
        """create an output file, filling it with contents."""
        fpath = self.getOutputFile(ext)
        fileOps.ensureFileDir(fpath)
        fh = open(fpath, "w")
        try:
            fh.write(contents)
        finally:
            fh.close()

    def verifyOutputFile(self, ext, expectContents=""):
        """verify an output file, if contents is not None, it is a string to
        compare to the expected contents of the file."""
        fpath = self.getOutputFile(ext)
        self.mustExist(fpath)
        self.failUnless(os.path.isfile(fpath))
        fh = open(fpath)
        try:
            got = fh.read()
        finally:
            fh.close()
        self.failUnlessEqual(got, expectContents)
