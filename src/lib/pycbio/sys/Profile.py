import hotshot, signal

sigProfObject = None

def sigHandler(signum, frame):
    "signal handler to stop logging and terminate process"
    sigProfObject.finishUp()
    sys.stderr("Warning: profiler exiting on signal\n")
    sys.exit(1)

class Profile(object):
    """support for profilling
    Adds cmd options:
       --profile=profFile
       --profile-sig=signal
       --profile-lines
    """

    def __init__(self, cmdParser):
        cmdParser.add_option("--profile", dest="profile", action="store",
                             default=None, type="string",
                             help="enable profiling, logging to this file")
        cmdParser.add_option("--profile-signal", dest="signal", action="store",
                             default=None, type="int",
                             help="specify signal number that will stop logging and exit program")
        cmdParser.add_option("--profile-lines",
                             action="store_true", dest="profileLines", default=False,
                             help="record line profiling information")
        self.profiler = None
        self.logFile = None
        self.signum = None

    def setup(self, opts):
        """initializing profiling, if requested"""
        if opts.profile == None:
            if opts.profileLines:
                raise Exception("can't specify --profile-lines without --profile")
            if opts.signal != None:
                raise Exception("can't specify --profile-signal without --profile")
        else:
            if opts.signal != None:
                global sigProfObject
                sigProfObject = self
                self.signum = opts.signal
                signal.signal(self.signum, sigHandler)
            self.logFile = opts.profile
            self.profiler = hotshot.Profile(self.logFile, lineevents=opts.profileLines)
            # FIXME: start/stop doesn't work, use ;            # prof.runcall(
            # http://bugs.python.org/issue1019882
            # self.profiler.start()

    def finishUp(self):
        "if profiling is enabled, stop and close log file"
        if self.profiler != None:
            # FIXME: self.profiler.stop()
            self.profiler.close()
            if self.signum != None:
                signal.signal(self.signum, signal.SIG_IGN)
                sigProfObject = None
                self.signum = None
