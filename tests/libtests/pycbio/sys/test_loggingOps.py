# Copyright 2006-2025 Mark Diekhans
import sys
import logging
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from logging.handlers import SysLogHandler
from pycbio.sys import loggingOps

def testFacilityLower():
    assert loggingOps.parseFacility("daemon") == SysLogHandler.LOG_DAEMON

def testFacilityUpper():
    assert loggingOps.parseFacility("DAEMON") == SysLogHandler.LOG_DAEMON

def testFacilityInvalid():
    with pytest.raises(ValueError, match='^invalid syslog facility: "Fred"$'):
        loggingOps.parseFacility("Fred")

def testLevelLower():
    assert loggingOps.parseLevel("info") == logging.INFO

def testLevelUpper():
    assert loggingOps.parseLevel("INFO") == logging.INFO

def testLevelInvalid():
    with pytest.raises(ValueError, march='^invalid logging level: "Fred"$'):
        loggingOps.parseLevel("Fred")
