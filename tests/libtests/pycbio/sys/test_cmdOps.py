# Copyright 2006-2025 Mark Diekhans
"""Miscellaneous command line parsing operations tests"""
import sys
import os.path as osp
import unittest
import argparse
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import cmdOps

class ArgParserNoExit(argparse.ArgumentParser):
    "raises exception rather than exit"
    def error(self, message):
        raise argparse.ArgumentError(None, message)

def makeTrekParser():
    parser = ArgParserNoExit(description='to go where no one has gone before')
    parser.add_argument('--kirk', type=int)
    parser.add_argument('--spock', '-s', type=str)
    parser.add_argument('-m', '--mc-coy', dest='mc_coy', type=str)
    parser.add_argument('-u', dest='uhura', action='store_true')
    parser.add_argument('barney')
    return parser

class CmdOpsTests(TestCaseBase):
    def _checkTrekOpts(self, opts, kirk, spock, mc_coy, uhura):
        self.assertEqual(opts.kirk, kirk)
        self.assertEqual(opts.spock, spock)
        self.assertEqual(opts.mc_coy, mc_coy)
        self.assertEqual(opts.uhura, uhura)

    def testGetOptsLong(self):
        parser = makeTrekParser()
        testargs = ('--kirk=10', '--spock=fred', 'foo')
        args = parser.parse_args(testargs)
        opts = cmdOps.getOptionalArgs(parser, args)
        self._checkTrekOpts(opts, 10, 'fred', None, False)

    def testGetOptsShort(self):
        parser = makeTrekParser()
        testargs = ('-s' 'fred', '-m', 'barney', '-u', 'baz')
        args = parser.parse_args(testargs)
        opts = cmdOps.getOptionalArgs(parser, args)
        self._checkTrekOpts(opts, None, 'fred', 'barney', True)

class ErrorHandlerTests(TestCaseBase):
    PRINT_CMD = True

    ##
    # matches to cmdOpsTestProg output
    ##
    _userCausedMsgExpect = (
        'UserCausedException: bad user\n'
        '  Caused by: RuntimeError: two caught\n'
        '    Caused by: ValueError: bad, bad value\n'
        'Specify --log-debug for details\n')
    _userCausedStackExpect = (
        r'^Traceback.+cmdOpsTestProg.+ValueError: bad, bad value\n'
        r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
        r'.+UserCausedException: bad user' '\n$')
    _bugMsgExpect = (
        'BugException: bad software\n'
        '  Caused by: RuntimeError: two caught\n'
        '    Caused by: ValueError: bad, bad value\n'
        'Specify --log-debug for details\n')
    _bugStackExpect = (
        r'^Traceback.+cmdOpsTestProg.+ValueError: bad, bad value\n'
        r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
        r'.+BugException: bad software' '\n$')
    _annoyMsgExpect = (
        'AnnoyingException: very annoying\n'
        '  Caused by: RuntimeError: two caught\n'
        '    Caused by: ValueError: bad, bad value\n'
        'Specify --log-debug for details\n')
    _annoyStackExpect = (
        r'^Traceback.+cmdOpsTestProg.+ValueError: bad, bad value\n'
        r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
        r'.+AnnoyingException: very annoying' '\n$')
    _fileNotFoundMsgExpect = (
        'FileNotFoundError: /dev/fred/barney\n'
        'Specify --log-debug for details\n')

    def _runCmdHandlerTestProg(self, errorWrap, *, errorClass=None,
                               printStackFilter=None, debugLog=False):
        cmd = [sys.executable, osp.join(self.getTestDir(), "bin/cmdOpsTestProg")]
        if errorClass is not None:
            cmd.append("--error-class=" + errorClass)
        if printStackFilter is not None:
            cmd.append("--print-stack-filter=" + printStackFilter)
        if debugLog:
            cmd.append("--log-level=DEBUG")
        cmd.append(errorWrap)
        try:
            if self.PRINT_CMD:
                print("DEBUG", ' '.join(cmd), file=sys.stderr)
            pipettor.run(cmd)
            return (0, None)
        except pipettor.ProcessException as ex:
            return ex.returncode, ex.stderr

    def testCmdHanderOkay(self):
        returncode, stderr = self._runCmdHandlerTestProg('no_wrap', errorClass='no_error')
        self.assertEqual(None, stderr)
        self.assertEqual(0, returncode)

    def testCmdHanderUser(self):
        returncode, stderr = self._runCmdHandlerTestProg('no_stack')
        self.assertEqual(self._userCausedMsgExpect, stderr)
        self.assertEqual(1, returncode)

    def testCmdHanderUserStack(self):
        returncode, stderr = self._runCmdHandlerTestProg('no_stack', debugLog=True)
        self.assertRegexDotAll(stderr, self._userCausedStackExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderBug(self):
        returncode, stderr = self._runCmdHandlerTestProg('with_stack')
        self.assertRegexDotAll(stderr, self._bugStackExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderNoStackExcepts(self):
        returncode, stderr = self._runCmdHandlerTestProg('no_stack_excepts')
        self.assertEqual(stderr, self._annoyMsgExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderFileNotFound(self):
        returncode, stderr = self._runCmdHandlerTestProg('no_wrap', errorClass='file_not_found')
        self.assertEqual(stderr, self._fileNotFoundMsgExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderFilterTrue(self):
        returncode, stderr = self._runCmdHandlerTestProg('with_stack', printStackFilter="True")
        self.assertRegexDotAll(stderr, self._bugStackExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderFilterTrue2(self):
        # force even with NoStackError
        returncode, stderr = self._runCmdHandlerTestProg('no_stack', printStackFilter="True")
        self.assertRegexDotAll(stderr, self._userCausedStackExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderFilterFalse(self):
        returncode, stderr = self._runCmdHandlerTestProg('with_stack', printStackFilter="False")
        self.assertEqual(stderr, self._bugMsgExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderFilterNone(self):
        # all through to default handling
        returncode, stderr = self._runCmdHandlerTestProg('with_stack', printStackFilter="None")
        self.assertRegexDotAll(stderr, self._bugStackExpect)
        self.assertEqual(1, returncode)

    def testCmdHanderFilterNone2(self):
        # all through to default handling NoStackError
        returncode, stderr = self._runCmdHandlerTestProg('no_stack', printStackFilter="None")
        self.assertEqual(stderr, self._userCausedMsgExpect)
        self.assertEqual(1, returncode)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CmdOpsTests))
    ts.addTest(unittest.makeSuite(ErrorHandlerTests))
    return ts


if __name__ == '__main__':
    unittest.main()
