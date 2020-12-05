# Copyright 2006-2012 Mark Diekhans
import os
import sys
import unittest
import difflib
import threading
import errno
import re
import glob
import subprocess
import traceback
import warnings
from pipes import quote
from pycbio.sys import fileOps
from pycbio.hgdata.hgConf import HgConf


try:
    MAXFD = os.sysconf("SC_OPEN_MAX")
except ValueError:
    MAXFD = 256


def _warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    log = file if hasattr(file, 'write') else sys.stderr
    traceback.print_stack(file=log)
    log.write(warnings.formatwarning(message, category, filename, lineno, line))


def enable_warning_traceback():
    """Enable trace-back warnings to debug test issues"""
    warnings.showwarning = _warn_with_traceback


class TestCaseBase(unittest.TestCase):
    """Base class for test case with various test support functions"""

    def __init__(self, methodName='runTest'):
        """initialize, removing old output files associated with the class"""
        super(TestCaseBase, self).__init__(methodName)
        clId = self.getClassId()
        od = self.getOutputDir()
        for f in glob.glob(os.path.join(od, "/{}.*".format(clId))) + glob.glob(os.path.join(od, "/tmp.*.{}.*".format(clId))):
            fileOps.rmTree(f)

    def getClassId(self):
        """Get the first part of the portable test id, consisting
        moduleBase.class.  This is the prefix to output files"""
        # module name is __main__ when run standalone, so get base file name
        mod = os.path.splitext(os.path.basename(sys.modules[self.__class__.__module__].__file__))[0]
        return mod + "." + self.__class__.__name__

    def getId(self):
        """get the fixed test id, which is in the form moduleBase.class.method
        which avoids different ids when test module is run as main or
        from a larger program"""
        # last part of unittest id is method
        return self.getClassId() + "." + self.id().split(".")[-1]

    @classmethod
    def getTestDir(cls):
        """Find test directory, where concrete class is defined, class method so can
        be used in class setUpClass"""
        testDir = os.path.dirname(sys.modules[cls.__module__].__file__)
        if testDir == "":
            testDir = "."
        testDir = os.path.realpath(testDir)
        # turn this into a relative directory
        cwd = os.getcwd()
        if testDir.startswith(cwd):
            testDir = testDir[len(cwd) + 1:]
            if len(testDir) == 0:
                testDir = "."
        return testDir

    @classmethod
    def getTestRelProg(cls, progName):
        "get path to a program in directory above the test directory"
        return os.path.join(cls.getTestDir(), "..", progName)

    @classmethod
    def getInputFile(cls, fname):
        """Get a path to a file in the test input directory"""
        return cls.getTestDir() + "/input/" + fname

    def getOutputDir(self):
        """get the path to the output directory to use for this test, create if it doesn't exist"""
        d = os.path.join(self.getTestDir(), "output")
        fileOps.ensureDir(d)
        return d

    def getOutputFile(self, ext):
        """Get path to the output file, using the current test id and append
        ext, which should contain a dot."""
        f = os.path.join(self.getOutputDir(), self.getId() + ext)
        return f

    def getExpectedFile(self, ext, basename=None):
        """Get path to the expected file, using the current test id and append
        ext. If basename is used, it is instead of the test id, allowing share
        an expected file between multiple tests."""
        return os.path.join(self.getTestDir(), "expected/{}{}".format(basename if basename is not None else self.getId(),
                                                                      ext))

    def _getLines(self, file):
        with open(file) as fh:
            return fh.readlines()

    def mustExist(self, path):
        if not os.path.exists(path):
            self.fail("file does not exist: " + path)

    def diffFiles(self, expFile, outFile):
        """diff expected and output files."""

        expLines = self._getLines(expFile)
        outLines = self._getLines(outFile)

        diff = list(difflib.unified_diff(expLines, outLines, expFile, outFile))
        for l in diff:
            print(l, end=' ')
        self.assertTrue(len(diff) == 0)

    def diffExpected(self, ext):
        """diff expected and output files, with names computed from test id."""
        self.diffFiles(self.getExpectedFile(ext), self.getOutputFile(ext))

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
        self.assertTrue(os.path.isfile(fpath))
        fh = open(fpath)
        try:
            got = fh.read()
        finally:
            fh.close()
        self.assertEqual(got, expectContents)

    @staticmethod
    def numRunningThreads():
        "get the number of threads that are running"
        n = 0
        for t in threading.enumerate():
            if t.isAlive():
                n += 1
        return n

    def assertSingleThread(self):
        "fail if more than one thread is running"
        self.assertEqual(self.numRunningThreads(), 1)

    def assertNoChildProcs(self):
        "fail if there are any running or zombie child process"
        ex = None
        try:
            s = os.waitpid(0, os.WNOHANG)
        except OSError as ex:
            if ex.errno != errno.ECHILD:
                raise
        if ex is None:
            self.fail("pending child processes or zombies: " + str(s))

    @staticmethod
    def numOpenFiles():
        "count the number of open files"
        n = 0
        for fd in range(0, MAXFD):
            try:
                os.fstat(fd)
            except OSError:
                n += 1
        return MAXFD - n

    def assertNumOpenFilesSame(self, prevNumOpen):
        "assert that the number of open files has not changed"
        numOpen = self.numOpenFiles()
        if numOpen != prevNumOpen:
            self.fail("number of open files changed, was " + str(prevNumOpen) + ", now it's " + str(numOpen))

    def assertRegexDotAll(self, obj, expectRe, msg=None):
        """Fail if the str(obj) does not match expectRe operator, including `.' matching newlines"""
        if not re.match(expectRe, str(obj), re.DOTALL):
            raise self.failureException(msg or "regexp '{}' does not match '{}'".format(expectRe, str(obj)))

    def _logCmd(self, cmd):
        cmdStrs = [quote(a) for a in cmd]
        sys.stderr.write("run: " + " ".join(cmdStrs) + "\n")

    def runProg(self, cmd, stdin=None, stdout=None, stderr=None):
        "run a program, print the command being executed"
        self._logCmd(cmd)
        subprocess.check_call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)

    def runProgOut(self, cmd, stdin=None, stderr=None):
        "run a program and return stdout, print the command being executed"
        self._logCmd(cmd)
        p = subprocess.Popen(cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)
        (stdoutText, junk) = p.communicate()
        exitCode = p.wait()
        if exitCode:
            raise subprocess.CalledProcessError(exitCode, cmd)
        return stdoutText

    def brokenOnOSX(self):
        "If this is OS/X, output message to indicate this test is broken and return True "
        # FIXME: this is temporary, not needed any more
        if sys.platform == "darwin":
            print("WARNING: test {} does not run on OS/X".format(self.id()), file=sys.stderr)
            return True
        else:
            return False

    warnedAboutHgConf = False

    def haveHgConf(self):
        "check for ~/hg.conf so test can be skipped without it. Warn if not available"
        try:
            HgConf()
            return True
        except FileNotFoundError:
            if not self.warnedAboutHgConf:
                msg = "WARNING: hg.conf not found, database tests disabled: {}".format(HgConf.getHgConf())
                print(msg, file=sys.stderr)
                self.skipTest(msg)
            return False
