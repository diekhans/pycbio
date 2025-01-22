# Copyright 2006-2025 Mark Diekhans
import cProfile
import signal
import sys
import atexit
from pycbio import PycbioException


class Profile:
    """Wrapper to make adding optional support for profiling easy.
    Adds cmd options:
       --profile=profFile
       --profile-sig=signal
    This works with both optparse and argparse.

    Serving suggestion:
        parser = argparse.ArgumentParser(description=desc)
        profiler = Profile(parser)
        ...
        args = parser.parse_args()
        ...
        profiler.setup(args)

    at the end of the program:
        profiler.finishup()
    or let exit handle call finishup()

    Use the program profStats to create reports.
    """

    def __init__(self, cmdParser):
        cmdParser.add_argument("--profile",
                               help="enable profiling, logging to this file")
        cmdParser.add_argument("--profile-signal", dest="profileSignal", default=None, type=int,
                               help="specify signal number that will stop logging and exit program")
        self.profiler = None
        self.logFile = None
        self.signum = None

    def _sigHandler(self, signum, frame):
        "signal handler to stop logging and terminate process"
        self.finishup()
        sys.stderr("Warning: profiler exiting on signal\n")
        sys.exit(1)

    def _setupSignalHandler(self, signum):
        self.signum = signum
        signal.signal(self.signum, self._sigHandler)

    def setup(self, args):
        """initializing profiling, if requested"""
        if args.profile is None:
            if args.profileSignal is not None:
                raise PycbioException("can't specify --profile-signal without --profile")
        else:
            if args.profileSignal is not None:
                self._setupSignalHandler(args.profileSignal)
            atexit.register(self.finishup)
            self.logFile = args.profile
            self.profiler = cProfile.Profile()
            self.profiler.enable()

    def _finishupSignal(self):
        signal.signal(self.signum, signal.SIG_IGN)
        self.signum = None

    def finishup(self):
        "if profiling is enabled, stop and close log file"
        if self.profiler is not None:
            self.profiler.disable()
            if self.signum is not None:
                self._finishupSignal()
            self.profiler.dump_stats(self.logFile)
