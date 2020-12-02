# Copyright 2006-2012 Mark Diekhans
import cProfile
import signal
import argparse
import sys
from pycbio.sys import PycbioException


class Profile(object):
    """Wrapper to make adding optional support for profiling easy.
    Adds cmd options:
       --profile=profFile
       --profile-sig=signal
    This works with both optparse and argparse.

    Serving suggestion:
        parser = OptionParser(usage=CmdOpts.usage)
        profiler = Profile(parser)
        ...
        (opts, args) = parser.parse_args()
        ...
        profiler.setup(opts)

    at the end of the program:
        profiler.finishUp()

    Use the program profStats to create reports.
    """

    def __init__(self, cmdParser):
        profileHelp = "enable profiling, logging to this file"
        profileSignalHelp = "specify signal number that will stop logging and exit program"
        if isinstance(cmdParser, argparse.ArgumentParser):
            cmdParser.add_argument("--profile", dest="profile", action="store", default=None, help=profileHelp)
            cmdParser.add_argument("--profile-signal", dest="signal", action="store", default=None, type=int, help=profileSignalHelp)
        else:
            cmdParser.add_option("--profile", dest="profile", action="store", default=None, help=profileHelp)
            cmdParser.add_option("--profile-signal", dest="signal", action="store", default=None, type="int", help=profileSignalHelp)
        self.profiler = None
        self.logFile = None
        self.signum = None

    def _sigHandler(self, signum, frame):
        "signal handler to stop logging and terminate process"
        self.finishUp()
        sys.stderr("Warning: profiler exiting on signal\n")
        sys.exit(1)

    def _setupSignalHandler(self, signum):
        self.signum = signum
        signal.signal(self.signum, self._sigHandler)

    def setup(self, opts):
        """initializing profiling, if requested"""
        if opts.profile is None:
            if opts.signal is not None:
                raise PycbioException("can't specify --profile-signal without --profile")
        else:
            if opts.signal is not None:
                self._setupSignalHandler(opts.signal)
            self.logFile = opts.profile
            self.profiler = cProfile.Profile()
            self.profiler.enable()

    def _finishupSignal(self):
        signal.signal(self.signum, signal.SIG_IGN)
        self.signum = None

    def finishUp(self):
        "if profiling is enabled, stop and close log file"
        if self.profiler is not None:
            self.profiler.disable()
            if self.signum is not None:
                self._finishupSignal()
            self.profiler.dump_stats(self.logFile)
