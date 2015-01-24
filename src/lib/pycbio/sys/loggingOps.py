"""
Operations associated with logging
"""
import logging
from logging.handlers import SysLogHandler


def parseFacility(facilityStr):
    "convert case-insensitive facility string to a facility number"
    facilityStrLower = facilityStr.lower()
    facility = SysLogHandler.facility_names.get(facilityStrLower)
    if facility == None:
        raise ValueError("invalid syslog facility: \"" + facilityStr + "\"")
    return facility

def parseLevel(levelStr):
    "convert a log level string to numeric value"
    levelStrUp = levelStr.upper()
    level = logging._levelNames.get(levelStrUp)
    if level == None:
        raise ValueError("invalid logging level: \"" + levelStr + "\"")
    return level

def setupLogger(handler):
    """add handle to logger and set logger level to the minimum of it's
    current and the handler level"""
    logger = logging.getLogger()
    logger.setLevel(min(handler.level, logger.level))
    logger.addHandler(handler)

def setupStreamLogger(level, fh):
    "configure logging to a specified open file."
    handler = logging.StreamHandler(stream=fh)
    handler.setLevel(level)
    setupLogger(handler)

def setupStderrLogger(level):
    "configure logging to stderr"
    setupStreamLogger(level, sys.stderr)

def setupSyslogLogger(facility, level, programName=None):
    """configure logging to syslog based on the specified facility.  If
    programName specified, each line is prefixed with the name"""
    handler = SysLogHandler(address="/dev/log", facility=facility)
    # add a formatter that includes the program name as the syslog ident
    if progName != None:
        handler.setFormatter(logging.Formatter(fmt=progName+" %(message)s"))
    handler.setLevel(level)
    setupLogger(handler)
    
