# Copyright 2006-2026 Mark Diekhans
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
    assert tlog.logger.level == logging.ERROR

def testSetupLoggerNoneLevel():
    "level=None must not drop a fresh logger to NOTSET; the handler level stands"
    logger = logging.getLogger("testSetupLoggerNoneLevel")
    assert logger.level == logging.NOTSET
    handler = logging.NullHandler()
    handler.setLevel(logging.ERROR)
    loggingOps.setupLogger(logger, handler, level=None)
    assert logger.level == logging.ERROR


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
    # line3 has no newline yet, so it is held for the write that completes it
    assert "line3" not in tlog.data
    stl.write("more\n")
    assert "line3more" in tlog.data

def testStreamToLoggerWritePartialLine():
    "a line split over two writes is one log record, not two"
    tlog = ts.LoggerForTests()
    stl = loggingOps.StreamToLogger(tlog.logger, logging.WARNING)
    stl.write("abc")
    stl.write("def\n")
    assert tlog.data == "abcdef\n"

def testStreamToLoggerFlushPartial():
    tlog = ts.LoggerForTests()
    stl = loggingOps.StreamToLogger(tlog.logger, logging.WARNING)
    stl.write("tail")
    assert tlog.data == ""
    stl.flush()
    assert tlog.data == "tail\n"

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

###
# --log-conf, and a handler left at NOTSET
###
def _writeLogConf(request):
    conf = ts.get_test_output_file(request, ".conf")
    with open(conf, "w") as fh:
        fh.write("[loggers]\nkeys=root\n"
                 "[handlers]\nkeys=h\n"
                 "[formatters]\nkeys=f\n"
                 "[logger_root]\nlevel=INFO\nhandlers=h\n"
                 "[handler_h]\nclass=StreamHandler\nlevel=INFO\nformatter=f\nargs=(sys.stderr,)\n"
                 "[formatter_f]\nformat=%(message)s\n")
    return conf

def testSetupFromCmdLogConf(request):
    """--log-conf calls logging.config.fileConfig, which needs logging.config
    imported; importing logging alone left it an AttributeError"""
    parser = argparse.ArgumentParser()
    loggingOps.addCmdOptions(parser)
    args = parser.parse_args(["--log-conf", _writeLogConf(request)])
    loggingOps.setupFromCmd(args)
    assert logging.getLogger().level == logging.INFO

def testSetupLoggerNotsetHandler():
    """a handler left at NOTSET must not pull the logger down with it: NOTSET is 0,
    so min(handler.level, level) was 0 and the level argument was discarded"""
    tlog = ts.LoggerForTests()
    handler = logging.StreamHandler()
    assert handler.level == logging.NOTSET
    loggingOps.setupLogger(tlog.logger, handler, level=logging.WARNING)
    assert tlog.logger.level == logging.WARNING

def testSetupLoggerHandlerLevelStillCaps():
    "a handler with a level of its own still lowers the logger to it"
    tlog = ts.LoggerForTests()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    loggingOps.setupLogger(tlog.logger, handler, level=logging.WARNING)
    assert tlog.logger.level == logging.DEBUG
