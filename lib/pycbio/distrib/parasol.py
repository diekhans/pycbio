# Copyright 2006-2025 Mark Diekhans
"""classes for interacting with parasol batch system"""
import shlex
import os.path
from pycbio import PycbioException
from pycbio.sys import fileOps
import pipettor

def _mkAbs(parent, child):
    if os.path.isabs(child):
        return child
    else:
        return os.path.join(parent, child)

class BatchStats:
    "statistics on jobs in the current batch"

    # map of `string: cnt' lines to fields
    _simpleParse = {"unsubmitted jobs": "unsubmitted",
                    "submission errors": "subErrors",
                    "queue errors": "queueErrors",
                    "tracking errors": "trackingErrors",
                    "queued and waiting": "waiting",
                    "crashed": "crashed",
                    "running": "running",
                    "ranOk": "ranOk",
                    "total jobs in batch": "totalJobs"}

    def _parseLine(self, words):
        fld = self._simpleParse.get(words[0])
        if fld is not None:
            setattr(self, fld, int(words[1]))
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

        # parse lines, skiping empty lines
        for line in lines:
            line = line.strip()
            if len(line) > 0:
                words = line.split(":")
                if (len(words) < 2) or not self._parseLine(words):
                    raise PycbioException("don't know how to parse para check output line: {}".format(line))

    def hasParasolErrs(self):
        return self.subErrors or self.queueErrors or self.trackingErrors or self.paraResultsErrors

    def succeeded(self):
        return (not self.hasParasolErrs()) and (self.ranOk == self.totalJobs)


class Para:
    "interface to the parasol para command"
    def __init__(self, *, paraHost=None, jobFile=None, runDir=None, paraDir=None, cpu=None, mem=None, maxJobs=None, retries=None):
        """"will chdir to runDir, which default to cwd.  paraDir should be relative
        to runDir or absolute, defaults to runDir to jobFile should be relative to runDir
        or absolute.
        """
        self.paraHost = paraHost
        # symlinks can confuse parasol, as it can give two different names for a job.
        if runDir is None:
            runDir = os.getcwd()
        self.runDir = os.path.realpath(os.path.abspath(runDir))
        if paraDir is None:
            paraDir = runDir
        self.paraDir = os.path.realpath(paraDir)
        self.jobFile = jobFile
        self.cpu = cpu
        self.mem = mem
        self.maxJobs = maxJobs
        self.retries = retries
        absJobFile = _mkAbs(self.runDir, self.jobFile)
        if not os.path.exists(absJobFile):
            raise PycbioException("job file not found: {}".format(absJobFile))
        fileOps.ensureDir(_mkAbs(self.runDir, self.paraDir))

    def _para(self, *paraArgs, stderr=pipettor.DataReader):
        """ssh to the remote machine and run the para command.  paraArgs are
        passed as arguments to the para command. Returns stdout as a list of
        lines, stderr in ProcException if the remote program encouners an
        error. There is a possibility for quoting hell here."""
        paraCmd = ["para", f"-batch={self.paraDir}"]
        for pa in paraArgs:
            paraCmd.append(shlex.quote(pa))
        if self.cpu is not None:
            paraCmd.append("-cpu={}".format(self.cpu))
        if self.mem is not None:
            paraCmd.append("-ram={}".format(self.mem))
        if self.maxJobs is not None:
            paraCmd.append("-maxJob={}".format(self.maxJobs))
        if self.retries is not None:
            paraCmd.append("-retries={}".format(self.retries))
        if self.paraHost is None:
            cmd = paraCmd
        else:
            remCmd = "cd {} && {}".format(shlex.quote(self.runDir), shlex.join(paraCmd))
            cmd = ["ssh", "-nx", "-o", "ClearAllForwardings=yes", self.paraHost, remCmd]
        return pipettor.runout(cmd, stderr=stderr).split('\n')

    def wasStarted(self):
        """check to see if it appears that the batch was started; this doens't mean
        it's currently running, or even succesfully started"""
        return os.path.exists(os.path.join(self.paraDir, "batch"))

    def make(self):
        "run para make"
        # want to keep status streaming to stderr
        self._para("make", self.jobFile, stderr='/dev/stderr')

    def check(self):
        "run para check and return statistics"
        lines = self._para("check", self.jobFile)
        return BatchStats(lines)

    def freeBatch(self):
        "free the batch, no-op if it doesn't exist"
        try:
            self._para("freeBatch")
        except pipettor.exceptions.ProcessException as ex:
            if ex.stderr.find("Batch not found") < 0:
                raise

    def clearSickNodes(self):
        "clearSickNodes for a batch, no-op if it doesn't exist"
        try:
            self._para("clearSickNodes")
        except pipettor.exceptions.ProcessException as ex:
            if ex.stderr.find("Batch not found") < 0:
                raise

    def time(self):
        "run para check and return statistics as a list of lines"
        return self._para("time")


__all__ = [BatchStats.__name__, Para.__name__]
