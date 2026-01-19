# Copyright 2006-2025 Mark Diekhans
import sys
import logging
import argparse
import io
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from logging.handlers import SysLogHandler
from pycbio.sys import loggingOps


class TestGetNames:
    def testGetFacilityNames(self):
        names = loggingOps.getFacilityNames()
        assert isinstance(names, tuple)
        assert "daemon" in names
        assert "local0" in names
        assert "user" in names

    def testGetLevelNames(self):
        names = loggingOps.getLevelNames()
        assert isinstance(names, tuple)
        assert "INFO" in names
        assert "DEBUG" in names
        assert "WARNING" in names
        assert "ERROR" in names


class TestParseFacility:
    def testFacilityLower(self):
        assert loggingOps.parseFacility("daemon") == SysLogHandler.LOG_DAEMON

    def testFacilityUpper(self):
        assert loggingOps.parseFacility("DAEMON") == SysLogHandler.LOG_DAEMON

    def testFacilityMixed(self):
        assert loggingOps.parseFacility("Daemon") == SysLogHandler.LOG_DAEMON

    def testFacilityLocal(self):
        assert loggingOps.parseFacility("local0") == SysLogHandler.LOG_LOCAL0

    def testFacilityInvalid(self):
        with pytest.raises(ValueError, match="^invalid syslog facility: 'Fred"):
            loggingOps.parseFacility("Fred")


class TestParseLevel:
    def testLevelLower(self):
        assert loggingOps.parseLevel("info") == logging.INFO

    def testLevelUpper(self):
        assert loggingOps.parseLevel("INFO") == logging.INFO

    def testLevelMixed(self):
        assert loggingOps.parseLevel("Info") == logging.INFO

    def testLevelDebug(self):
        assert loggingOps.parseLevel("DEBUG") == logging.DEBUG

    def testLevelWarning(self):
        assert loggingOps.parseLevel("WARNING") == logging.WARNING

    def testLevelIntegerString(self):
        assert loggingOps.parseLevel("20") == 20

    def testLevelIntegerStringCustom(self):
        assert loggingOps.parseLevel("15") == 15

    def testLevelInvalid(self):
        with pytest.raises(ValueError, match="^invalid logging level: `FRED'"):
            loggingOps.parseLevel("Fred")


class TestAddLevelName:
    def testAddLevelNameFred(self):
        """Test that custom level names added via logging.addLevelName work."""
        logging.addLevelName(25, "FRED")
        assert loggingOps.parseLevel("FRED") == 25
        assert loggingOps.parseLevel("fred") == 25
        assert "FRED" in loggingOps.getLevelNames()


class TestSetupLogger:
    @pytest.fixture
    def cleanLogger(self):
        """Create a fresh logger for testing and clean up after."""
        logger = logging.getLogger("test_logger_" + str(id(self)))
        yield logger
        # Clean up handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def testSetupLoggerWithHandler(self, cleanLogger):
        handler = logging.NullHandler()
        handler.setLevel(logging.DEBUG)
        result = loggingOps.setupLogger(cleanLogger, handler, level=logging.INFO)
        assert result is cleanLogger
        assert handler in cleanLogger.handlers
        assert cleanLogger.level == logging.DEBUG  # min of INFO and DEBUG

    def testSetupLoggerByName(self):
        handler = logging.NullHandler()
        result = loggingOps.setupLogger("test_named_logger", handler, level=logging.WARNING)
        assert isinstance(result, logging.Logger)
        assert result.name == "test_named_logger"
        # Clean up
        for h in result.handlers[:]:
            result.removeHandler(h)

    def testSetupLoggerWithFormatter(self, cleanLogger):
        handler = logging.NullHandler()
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        loggingOps.setupLogger(cleanLogger, handler, formatter=formatter)
        assert handler.formatter is formatter


class TestSetupStreamLogger:
    def testSetupStreamLogger(self):
        logger = logging.getLogger("test_stream_logger")
        stream = io.StringIO()
        result = loggingOps.setupStreamLogger(logger, stream, logging.INFO)
        assert result is logger
        # Verify handler was added
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)


class TestSetupStderrLogger:
    def testSetupStderrLogger(self):
        logger = logging.getLogger("test_stderr_logger")
        result = loggingOps.setupStderrLogger(logger, level=logging.WARNING)
        assert result is logger
        assert logger.level == logging.WARNING
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testSetupStderrLoggerDefault(self):
        result = loggingOps.setupStderrLogger("test_stderr_default")
        assert result.level == logging.INFO
        # Clean up
        for h in result.handlers[:]:
            result.removeHandler(h)


class TestSetupNullLogger:
    def testSetupNullLogger(self):
        logger = logging.getLogger("test_null_logger")
        result = loggingOps.setupNullLogger(logger)
        assert result is logger
        null_handlers = [h for h in logger.handlers if isinstance(h, logging.NullHandler)]
        assert len(null_handlers) >= 1
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testSetupNullLoggerWithLevel(self):
        logger = logging.getLogger("test_null_level")
        loggingOps.setupNullLogger(logger, level=logging.ERROR)
        # Note: setupNullLogger sets handler level but setupLogger defaults
        # logger level to INFO, then takes min(handler, logger) = INFO
        assert logger.level == logging.INFO
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)


class TestGetSyslogAddress:
    def testGetSyslogAddress(self):
        addr = loggingOps.getSyslogAddress()
        # Should return either a device path or localhost tuple
        assert addr is not None
        if isinstance(addr, str):
            assert addr in ("/dev/log", "/var/run/syslog")
        else:
            assert addr == ("localhost", 514)


class TestStreamToLogger:
    def testWrite(self):
        logger = logging.getLogger("test_stream_to_logger")
        logger.setLevel(logging.DEBUG)
        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        stl = loggingOps.StreamToLogger(logger, logging.INFO)
        stl.write("test message\n")

        output = stream.getvalue()
        assert "test message" in output

        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testWriteMultiline(self):
        logger = logging.getLogger("test_stream_multiline")
        logger.setLevel(logging.DEBUG)
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        stl = loggingOps.StreamToLogger(logger, logging.WARNING)
        stl.write("line1\nline2\nline3")

        output = stream.getvalue()
        assert "line1" in output
        assert "line2" in output
        assert "line3" in output

        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testFlush(self):
        logger = logging.getLogger("test_flush")
        stl = loggingOps.StreamToLogger(logger, logging.INFO)
        # flush should not raise
        stl.flush()


class TestCmdOptions:
    def testAddCmdOptions(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser)
        args = parser.parse_args([])
        assert hasattr(args, 'log_stderr')
        assert hasattr(args, 'log_level')
        assert hasattr(args, 'log_conf')
        assert hasattr(args, 'log_debug')

    def testAddCmdOptionsWithSyslog(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser, inclSyslog=True)
        args = parser.parse_args([])
        assert hasattr(args, 'syslog_facility')

    def testHaveCmdOptions(self):
        parser = argparse.ArgumentParser()
        assert not loggingOps.haveCmdOptions(parser)
        loggingOps.addCmdOptions(parser)
        assert loggingOps.haveCmdOptions(parser)

    def testSetupFromCmdDefault(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser)
        args = parser.parse_args([])
        logger = loggingOps.setupFromCmd(args, logger="test_cmd_logger")
        assert isinstance(logger, logging.Logger)
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testSetupFromCmdDebug(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser)
        args = parser.parse_args(['--log-debug'])
        logger = loggingOps.setupFromCmd(args, logger="test_cmd_debug")
        assert logger.level == logging.DEBUG
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testSetupFromCmdLevel(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser)
        args = parser.parse_args(['--log-level', 'ERROR'])
        logger = loggingOps.setupFromCmd(args, logger="test_cmd_level")
        assert logger.level == logging.ERROR
        # Clean up
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    def testCmdOptionsInvalidFacility(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser, inclSyslog=True)
        with pytest.raises(SystemExit):
            parser.parse_args(['--syslog-facility', 'invalid'])

    def testCmdOptionsInvalidLevel(self):
        parser = argparse.ArgumentParser()
        loggingOps.addCmdOptions(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(['--log-level', 'invalid'])
