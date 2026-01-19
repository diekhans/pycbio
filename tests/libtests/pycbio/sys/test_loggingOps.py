# Copyright 2006-2025 Mark Diekhans
import sys
import logging
import argparse
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from logging.handlers import SysLogHandler
from pycbio.sys import testingSupport as ts
from pycbio.sys import loggingOps


# getFacilityNames / getLevelNames tests

def testGetFacilityNames():
    names = loggingOps.getFacilityNames()
    assert isinstance(names, tuple)
    assert "daemon" in names
    assert "local0" in names
    assert "user" in names

def testGetLevelNames():
    names = loggingOps.getLevelNames()
    assert isinstance(names, tuple)
    assert "INFO" in names
    assert "DEBUG" in names
    assert "WARNING" in names
    assert "ERROR" in names


# parseFacility tests

def testParseFacilityLower():
    assert loggingOps.parseFacility("daemon") == SysLogHandler.LOG_DAEMON

def testParseFacilityUpper():
    assert loggingOps.parseFacility("DAEMON") == SysLogHandler.LOG_DAEMON

def testParseFacilityMixed():
    assert loggingOps.parseFacility("Daemon") == SysLogHandler.LOG_DAEMON

def testParseFacilityLocal():
    assert loggingOps.parseFacility("local0") == SysLogHandler.LOG_LOCAL0

def testParseFacilityInvalid():
    with pytest.raises(ValueError, match="^invalid syslog facility: 'Fred"):
        loggingOps.parseFacility("Fred")


# parseLevel tests

def testParseLevelLower():
    assert loggingOps.parseLevel("info") == logging.INFO

def testParseLevelUpper():
    assert loggingOps.parseLevel("INFO") == logging.INFO

def testParseLevelMixed():
    assert loggingOps.parseLevel("Info") == logging.INFO

def testParseLevelDebug():
    assert loggingOps.parseLevel("DEBUG") == logging.DEBUG

def testParseLevelWarning():
    assert loggingOps.parseLevel("WARNING") == logging.WARNING

def testParseLevelIntegerString():
    assert loggingOps.parseLevel("20") == 20

def testParseLevelIntegerStringCustom():
    assert loggingOps.parseLevel("15") == 15

def testParseLevelInvalid():
    with pytest.raises(ValueError, match="^invalid logging level: `FRED'"):
        loggingOps.parseLevel("Fred")


# addLevelName tests

def testAddLevelNameFred():
    """Test that custom level names added via logging.addLevelName work."""
    logging.addLevelName(25, "FRED")
    assert loggingOps.parseLevel("FRED") == 25
    assert loggingOps.parseLevel("fred") == 25
    assert "FRED" in loggingOps.getLevelNames()


# setupLogger tests

def testSetupLoggerWithHandler():
    tlog = ts.LoggerForTests()
    handler = logging.NullHandler()
    handler.setLevel(logging.DEBUG)
    result = loggingOps.setupLogger(tlog.logger, handler, level=logging.INFO)
    assert result is tlog.logger
    assert handler in tlog.logger.handlers
    assert tlog.logger.level == logging.DEBUG  # min of INFO and DEBUG

def testSetupLoggerByName():
    handler = logging.NullHandler()
    result = loggingOps.setupLogger("test_named_logger", handler, level=logging.WARNING)
    assert isinstance(result, logging.Logger)
    assert result.name == "test_named_logger"

def testSetupLoggerWithFormatter():
    tlog = ts.LoggerForTests()
    handler = logging.NullHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    loggingOps.setupLogger(tlog.logger, handler, formatter=formatter)
    assert handler.formatter is formatter


# setupStreamLogger tests

def testSetupStreamLogger():
    tlog = ts.LoggerForTests()
    result = loggingOps.setupStreamLogger(tlog.logger, sys.stderr, logging.INFO)
    assert result is tlog.logger
    stream_handlers = [h for h in tlog.logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) >= 1


# setupStderrLogger tests

def testSetupStderrLogger():
    tlog = ts.LoggerForTests()
    result = loggingOps.setupStderrLogger(tlog.logger, level=logging.WARNING)
    assert result is tlog.logger
    assert tlog.logger.level == logging.WARNING

def testSetupStderrLoggerDefault():
    result = loggingOps.setupStderrLogger("test_stderr_default_" + str(id(testSetupStderrLoggerDefault)))
    assert result.level == logging.INFO


# setupNullLogger tests

def testSetupNullLogger():
    tlog = ts.LoggerForTests()
    result = loggingOps.setupNullLogger(tlog.logger)
    assert result is tlog.logger
    null_handlers = [h for h in tlog.logger.handlers if isinstance(h, logging.NullHandler)]
    assert len(null_handlers) >= 1

def testSetupNullLoggerWithLevel():
    tlog = ts.LoggerForTests()
    loggingOps.setupNullLogger(tlog.logger, level=logging.ERROR)
    # Note: setupNullLogger sets handler level but setupLogger defaults
    # logger level to INFO, then takes min(handler, logger) = INFO
    assert tlog.logger.level == logging.INFO


# getSyslogAddress tests

def testGetSyslogAddress():
    addr = loggingOps.getSyslogAddress()
    assert addr is not None
    if isinstance(addr, str):
        assert addr in ("/dev/log", "/var/run/syslog")
    else:
        assert addr == ("localhost", 514)


# StreamToLogger tests

def testStreamToLoggerWrite():
    tlog = ts.LoggerForTests()
    stl = loggingOps.StreamToLogger(tlog.logger, logging.INFO)
    stl.write("test message\n")
    assert "test message" in tlog.data

def testStreamToLoggerWriteMultiline():
    tlog = ts.LoggerForTests()
    stl = loggingOps.StreamToLogger(tlog.logger, logging.WARNING)
    stl.write("line1\nline2\nline3")
    assert "line1" in tlog.data
    assert "line2" in tlog.data
    assert "line3" in tlog.data

def testStreamToLoggerFlush():
    tlog = ts.LoggerForTests()
    stl = loggingOps.StreamToLogger(tlog.logger, logging.INFO)
    stl.flush()  # should not raise


# Command options tests

def testAddCmdOptions():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser)
    args = parser.parse_args([])
    assert hasattr(args, 'log_stderr')
    assert hasattr(args, 'log_level')
    assert hasattr(args, 'log_conf')
    assert hasattr(args, 'log_debug')

def testAddCmdOptionsWithSyslog():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser, inclSyslog=True)
    args = parser.parse_args([])
    assert hasattr(args, 'syslog_facility')

def testHaveCmdOptions():
    parser = argparse.ArgumentParser()
    assert not loggingOps.haveCmdOptions(parser)
    loggingOps.addCmdOptions(parser)
    assert loggingOps.haveCmdOptions(parser)

def testSetupFromCmdDefault():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser)
    args = parser.parse_args([])
    logger = loggingOps.setupFromCmd(args, logger="test_cmd_logger_" + str(id(testSetupFromCmdDefault)))
    assert isinstance(logger, logging.Logger)

def testSetupFromCmdDebug():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser)
    args = parser.parse_args(['--log-debug'])
    logger = loggingOps.setupFromCmd(args, logger="test_cmd_debug_" + str(id(testSetupFromCmdDebug)))
    assert logger.level == logging.DEBUG

def testSetupFromCmdLevel():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser)
    args = parser.parse_args(['--log-level', 'ERROR'])
    logger = loggingOps.setupFromCmd(args, logger="test_cmd_level_" + str(id(testSetupFromCmdLevel)))
    assert logger.level == logging.ERROR

def testCmdOptionsInvalidFacility():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser, inclSyslog=True)
    with pytest.raises(SystemExit):
        parser.parse_args(['--syslog-facility', 'invalid'])

def testCmdOptionsInvalidLevel():
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser)
    with pytest.raises(SystemExit):
        parser.parse_args(['--log-level', 'invalid'])
