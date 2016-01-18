"""
Operations associated with logging
"""
import logging, os, sys
from logging.handlers import SysLogHandler


def parseFacility(facilityStr):
    "convert case-insensitive facility string to a facility number"
    facilityStrLower = facilityStr.lower()
    facility = SysLogHandler.facility_names.get(facilityStrLower)
    if facility is None:
        raise ValueError("invalid syslog facility: \"" + facilityStr + "\"")
    return facility

def parseLevel(levelStr):
    "convert a log level string to numeric value"
    levelStrUp = levelStr.upper()
    level = logging._levelNames.get(levelStrUp)
    if level is None:
        raise ValueError("invalid logging level: \"" + levelStr + "\"")
    return level

def setupLogger(handler):
    """add handle to logger and set logger level to the minimum of it's
    current and the handler level"""
    logger = logging.getLogger()
    if handler.level is not None:
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

def getSyslogAddress():
    """find the address to use for syslog"""
    for dev in ("/dev/log", "/var/run/syslog"):
        if os.path.exists(dev):
            return dev
    return ("localhost", 514)
    
def setupSyslogLogger(facility, level, prog=None, address=None):
    """configure logging to syslog based on the specified facility.  If
    prog specified, each line is prefixed with the name"""
    if address is None:
        address = getSyslogAddress()
    handler = SysLogHandler(address=address, facility=facility)
    # add a formatter that includes the program name as the syslog ident
    if prog is not None:
        handler.setFormatter(logging.Formatter(fmt=prog+" %(message)s"))
    handler.setLevel(level)
    setupLogger(handler)
    
def setupNullLogger(level=None):
    "configure discard logging"
    handler = logging.NullHandler()
    if level is not None:
        handler.setLevel(level)
    setupLogger(handler)
                                    
def addCmdOptions(parser):
    """
    Add command line options related to logging
    """
    parser.add_argument("--syslogFacility", type=parseFacility,
                        help="Set syslog facility to case-insensitive symbolic value, if not specified, logging is not done to stderr, "
                        " one of {}".format(
                            ", ".join(SysLogHandler.facility_names.iterkeys())))
    parser.add_argument("--logLevel", default="warn", type=parseLevel,
                        help="Set level to case-insensitive symbolic value, one of {}".format(
                            ", ".join([n for n in logging._levelNames.itervalues() if isinstance(n, str)])))

def setupFromCmd(opts, prog=None):
    """configure logging based on command options.  If prog is specified, then
    the user it to set syslog program name.  This can be obtained from parser.prog.

    N.B: logging must be initialized after daemonization
    """
    if opts.syslogFacility is not None:
        setupSyslogLogger(opts.syslogFacility, opts.logLevel, prog=prog)
    else:
        setupStderrLogger(opts.logLevel)
        
