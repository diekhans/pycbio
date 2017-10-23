# Copyright 2006-2014 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")
import logging
from logging.handlers import SysLogHandler
from pycbio.sys import loggingOps
from pycbio.sys.testCaseBase import TestCaseBase
import argparse


class LoggingOpsTests(TestCaseBase):
    def testFacilityLower(self):
        self.assertEqual(loggingOps.parseFacility("daemon"), SysLogHandler.LOG_DAEMON)

    def testFacilityUpper(self):
        self.assertEqual(loggingOps.parseFacility("DAEMON"), SysLogHandler.LOG_DAEMON)

    def testFacilityInvalid(self):
        with self.assertRaisesRegex(ValueError, '^invalid syslog facility: "Fred"$'):
            loggingOps.parseFacility("Fred")

    def testLevelLower(self):
        self.assertEqual(loggingOps.parseLevel("info"), logging.INFO)

    def testLevelUpper(self):
        self.assertEqual(loggingOps.parseLevel("INFO"), logging.INFO)

    def testLevelInvalid(self):
        with self.assertRaisesRegex(ValueError, '^invalid logging level: "Fred"$'):
            loggingOps.parseLevel("Fred")

def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(LoggingOpsTests))
    return ts


if __name__ == '__main__':
    unittest.main()
