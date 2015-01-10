# Copyright 2006-2012 Mark Diekhans
import cProfile, signal, argparse

class Profile(object):
    """Wrapper to make adding optional support for profiling easy.
    Adds cmd options:
       --profile=profFile
       --profile-sig=signal
       --profile-lines

    Serving suggestion:
        parser = OptionParser(usage=CmdOpts.usage)
        self.profiler = Profile(parser)
        ...
        (opts, args) = parser.parse_args()
        ...
        self.profiler.setup(opts)
    
    at the end of the program:
        xxx.profiler.finishUp()

    Use the program profStats to create reports.  This works with both optparse and argparse
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

    def __sigHandler(self, signum, frame):
        "signal handler to stop logging and terminate process"
        self.finishUp()
        sys.stderr("Warning: profiler exiting on signal\n")
        sys.exit(1)

    def __setupSignalHandler(self, signum):
        self.signum = signum
        signal.signal(self.signum, self.__sigHandler)
        
    def setup(self, opts):
        """initializing profiling, if requested"""
        if opts.profile == None:
            if opts.signal != None:
                raise Exception("can't specify --profile-signal without --profile")
        else:
            if opts.signal != None:
                self.__setupSignalHandler(opts.signal)
            self.logFile = opts.profile
            self.profiler = cProfile.Profile()
            self.profiler.enable()

    def __finishupSignal(self):
        signal.signal(self.signum, signal.SIG_IGN)
        self.signum = None
                
    def finishUp(self):
        "if profiling is enabled, stop and close log file"
        if self.profiler != None:
            self.profiler.disable()
            if self.signum != None:
                self.__finishupSignal()
            self.profiler.dump_stats(self.logFile)
                
