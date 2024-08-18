# Copyright 2006-2022 Mark Diekhans
"""Miscellaneous command line parsing operations tests"""
import sys
import unittest
import argparse
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.sys import cmdOps

class TestArgParser(argparse.ArgumentParser):
    "raises exception rather than exit"
    def error(self, message):
        raise argparse.ArgumentError(None, message)

def makeTrekParser():
    parser = TestArgParser(description='to go where no one has gone before')
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

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(CmdOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
