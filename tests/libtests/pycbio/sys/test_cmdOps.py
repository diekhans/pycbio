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

    def _runCmdHandlerTestProg(self, *, noError=False, noStack=False, debugLog=False):
        cmd = [sys.executable, osp.join(self.getTestDir(), "./bin/cmdOpsTestProg")]
        if noError:
            cmd.append("--no-error")
        if noStack:
            cmd.append("--no-stack")
        if debugLog:
            cmd.append("--log-level=DEBUG")
        try:
            pipettor.run(cmd)
            return (0, None)
        except pipettor.ProcessException as ex:
            return ex.returncode, ex.stderr

    def testCmdHanderOkay(self):
        returncode, stderr = self._runCmdHandlerTestProg(noError=True)
        self.assertEqual(None, stderr)
        self.assertEqual(0, returncode)

    def testCmdHanderUser(self):
        expect = ("UserCausedException: bad user\n"
                  "  Caused by: RuntimeError: two caught\n"
                  "    Caused by: ValueError: bad, bad value\n")
        returncode, stderr = self._runCmdHandlerTestProg(noStack=True)
        self.assertEqual(expect, stderr)
        self.assertEqual(1, returncode)

    def testCmdHanderUserStack(self):
        expect = (r'^Traceback.+cmdOpsTestProg.+ValueError: bad, bad value\n'
                  r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
                  r'.+UserCausedException: bad user\n$')
        returncode, stderr = self._runCmdHandlerTestProg(noStack=True, debugLog=True)
        self.assertRegexDotAll(stderr, expect)
        self.assertEqual(1, returncode)

    def testCmdHanderBug(self):
        expect = (r'^Traceback.+cmdOpsTestProg.+ValueError: bad, bad value\n'
                  r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
                  r'.+BugException: bad software\n$')
        returncode, stderr = self._runCmdHandlerTestProg(noStack=False)
        self.assertRegexDotAll(stderr, expect)
        self.assertEqual(1, returncode)


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CmdOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
