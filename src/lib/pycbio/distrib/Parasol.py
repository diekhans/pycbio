"""classes for interacting with parasol batch system"""
from pycbio.sys import procOps

# FIXME: shell has multiple quoting hell issues; maybe something like 
# fsh (http://www.lysator.liu.se/fsh/) would fix this, and make it faster.
# or maybe netpipes, or libssh

class BatchStats(object):
    "statistics on jobs in the current batch"

    # map of `string: cnt' lines to fields
    _simpleParse = {"unsubmitted jobs":    "unsubmitted",
                    "submission errors":   "subErrors",
                    "queue errors":        "queueErrors",
                    "tracking errors":     "trackingErrors",
                    "queued and waiting":  "waiting",
                    "crashed":             "crashed",
                    "running":             "running",
                    "ranOk":               "ranOk",
                    "total jobs in batch": "totalJobs"}

    def _parseLine(self, words):
        fld = self._simpleParse.get(words[0])
        if fld != None:
            self.__dict__[fld] = int(words[1])
            return True
        elif words[0] == "para.results":
            self.paraResultsErrors = 1
            return True
        elif words[0].startswith("slow"):
            self.slow = int(words[1])
            return True
        elif words[0].startswith("hung"):
            self.hung = 0
            return True
        elif words[0].startswith("failed"):
            self.failed = 0
            return True
        else:
            return False

    def __init__(self, lines):
        "parse file given output lines of para check"
        # simple parse
        self.unsubmitted = 0
        self.subErrors = 0
        self.queueErrors = 0
        self.trackingErrors = 0
        self.waiting = 0
        self.crashed = 0
        self.running = 0
        self.ranOk = 0
        self.totalJobs = 0
        # special cases
        self.paraResultsErrors = 0
        self.slow = 0
        self.hung = 0
        self.failed = 0

        for line in lines:
            words = line.split(":")
            if (len(words) < 2) || not self._parseLine(words):
                raise Exception("don't know how to parse para check output line: "+line)

    def hasParasolErrs(self):
        return self.subErrors or self.queueErrors or self.trackingErrors or self.paraResultsErrors
    
    def succeeded(self):
        return (not hasParasolErrs()) and (self.runOk == self.totalJobs)
        
class Para(object):
    "interface to the parasol para command"
    def __init__(self, paraHost, paraDir, jobFile=None):
        "job file should be relative to paraDir"
        self.paraHost = paraHost
        self.paraDir = paraDir
        self.jobFile = jobFile

    def _para(self, *paraArgs):
        """ssh to the remote machine and run the para command.  paraArgs are
        passed as arguments to the para command. Returns stdout as a list of
        lines, stderr in ProcException if the remote program encouners an
        error. There is a possibility for quoting hell here."""
        remCmd = "cd " + self.paraDir + "; para " + " ".join(paraArgs)
        self.verb.pr(verb.trace, "ssh ", self.paraHost, " ", remCmd)
        return procOps.callProcLines(["ssh", "-o", "ClearAllForwardings=yes", self.paraHost, remCmd])

    def wasStarted(self):
        """check to see if it appears that the batch was started; this doens't mean
        it's currently running, or even succesfully started"""
        return os.path.exists(self.paraDir + "/batch")

    def make(self):
        "run para make"
        self._para("make", self.jobFile)

    def shove(self):
        "run para make"
        self._para("shove")

    def check(self):
        "run para check and return statistics"
        lines = self._para("make", self.jobFile)
        return BatchStats(lines)

__all__ = [BatchStats.__name__, Para.__name__]
