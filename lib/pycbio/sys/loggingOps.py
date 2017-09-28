"""
Operations associated with logging
"""
import logging
import os
import sys
from logging.handlers import SysLogHandler


# FIXME: need to be able to specify logger name,
# FIXME: this really needs rethought


def parseFacility(facilityStr):
    """convert case-insensitive facility string to a facility number."""
    facility = SysLogHandler.facility_names.get(facilityStr.lower())
    if facility is None:
        raise ValueError("invalid syslog facility: \"" + facilityStr + "\"")
    return facility


def parseLevel(levelStr):
    "convert a log level string to numeric value"
    levelStrUp = levelStr.toupper()
    level = logging._levelNames.get(levelStrUp)
    if level is None:
        raise ValueError("invalid logging level: \"" + levelStr + "\"")
    return level


def _convertFacility(facility):
    """convert facility from string to number, if not already a number"""
    return facility if isinstance(facility, int) else parseFacility(facility)


def _convertLevel(level):
    """convert level from string to number, if not already a number"""
    return level if isinstance(level, int) else parseLevel(level)


def setupLogger(handler, formatter=None):
    """add handle to logger and set logger level to the minimum of it's
    current and the handler level"""
    logger = logging.getLogger()
    if handler.level is not None:
        logger.setLevel(min(handler.level, logger.level))
    logger.addHandler(handler)
    if formatter is not None:
        handler.setFormatter(formatter)


def setupStreamLogger(fh, level, formatter=None):
    "configure logging to a specified open file."
    handler = logging.StreamHandler(stream=fh)
    handler.setLevel(_convertLevel(level))
    setupLogger(handler, formatter)


def setupStderrLogger(level, formatter=None):
    "configure logging to stderr"
    setupStreamLogger(sys.stderr, _convertLevel(level), formatter)


def getSyslogAddress():
    """find the address to use for syslog"""
    for dev in ("/dev/log", "/var/run/syslog"):
        if os.path.exists(dev):
            return dev
    return ("localhost", 514)


def setupSyslogLogger(facility, level, prog=None, address=None, formatter=None):
    """configure logging to syslog based on the specified facility.  If
    prog specified, each line is prefixed with the name"""
    if address is None:
        address = getSyslogAddress()
    handler = SysLogHandler(address=address, facility=facility)
    # add a formatter that includes the program name as the syslog ident
    if prog is not None:
        handler.setFormatter(logging.Formatter(fmt="{} %(message)s".format(prog)))
    handler.setLevel(level)
    setupLogger(handler, formatter)


def setupNullLogger(level=None):
    "configure discard logging"
    handler = logging.NullHandler()
    if level is not None:
        handler.setLevel(_convertLevel(level))
    setupLogger(handler)


def addCmdOptions(parser):
    """
    Add command line options related to logging.  None of these are defaulted,
    as one might need to determine if they were explicitly set. The use case
    being getting a value from a configuration file if it is not specified on
    the command line.
    """
    parser.add_argument("--syslogFacility", type=parseFacility,
                        help="Set syslog facility to case-insensitive symbolic value, if not specified, logging is not done to stderr, "
                        " one of {}".format(
                            ", ".join(SysLogHandler.facility_names.iterkeys())))
    parser.add_argument("--logLevel", type=parseLevel,
                        help="Set level to case-insensitive symbolic value, one of {}".format(
                            ", ".join([n for n in logging._levelNames.itervalues() if isinstance(n, str)])))
    parser.add_argument("--logConfFile",
                        help="Python logging configuration file, see logging.config.fileConfig()")


def setupFromCmd(opts, prog=None):
    """configure logging based on command options. Prog is used it to set the
    syslog program name. If prog is not specified, it is obtained from sys.arg.

    N.B: logging must be initialized after daemonization
    """
    if prog is None:
        prog = os.path.basesname(sys.argv[0])
    if opts.syslogFacility is not None:
        setupSyslogLogger(opts.syslogFacility, opts.logLevel, prog=prog)
    else:
        setupStderrLogger(opts.logLevel)
    if opts.logConfFile is not None:
        logging.config.fileConfig(opts.logConfFile)
