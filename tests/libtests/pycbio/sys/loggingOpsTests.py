# Copyright 2006-2014 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../..")
from pycbio.sys import loggingOps
from pycbio.sys.testCaseBase import TestCaseBase
import argparse


class LoggingOpsTests(TestCaseBase):
    def testFacilityLower(self):
        self.assertEqual(loggingOps.parseFacility("daemon"), 3)

    def testFacilityUpper(self):
        self.assertEqual(loggingOps.parseFacility("DAEMON"), 3)

    def testFacilityInvalid(self):
        with self.assertRaisesRegexp(ValueError, '^invalid syslog facility: "Fred"$'):
            loggingOps.parseFacility("Fred")

    def testLevelLower(self):
        self.assertEqual(loggingOps.parseLevel("info"), 20)

    def testLevelUpper(self):
        self.assertEqual(loggingOps.parseLevel("INFO"), 20)

    def testLevelInvalid(self):
        with self.assertRaisesRegexp(ValueError, '^invalid logging level: "Fred"$'):
            loggingOps.parseLevel("Fred")

    def __mkParser(self):
        parser = argparse.ArgumentParser(description="test")
        loggingOps.addCmdOptions(parser)
        return parser

    def testParseArgsFacility(self):
        opts = self.__mkParser().parse_args(["--syslogFacility=local0"])
        self.assertEqual(opts.syslogFacility, loggingOps.parseFacility("local0"))
        self.assertEqual(opts.logLevel, loggingOps.parseLevel("warn"))

    def testParseArgsFacilityLevel(self):
        opts = self.__mkParser().parse_args(["--syslogFacility=local1", "--logLevel=info"])
        self.assertEqual(opts.syslogFacility, loggingOps.parseFacility("local1"))
        self.assertEqual(opts.logLevel, loggingOps.parseLevel("info"))


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(LoggingOpsTests))
    return ts

if __name__ == '__main__':
    unittest.main()
