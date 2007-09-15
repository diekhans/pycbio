"File-like object to create and manage a pipeline of subprocesses"

# FIXME: should use mixins to!!
# FIXME: should move procOps exception to here, have option to throw stderr

import os, stat, subprocess, signal
from pycbio.sys import strOps, fileOps

# FIXME: do with regexp
def hasWhiteSpace(word):
    "check if a string contains any whitespace"
    for c in word:
        if c.isspace():
            return True
    return False

def setSigPipe():
    "enable sigpipe exit in current process"
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    if signal.getsignal(signal.SIGPIPE) != signal.SIG_DFL:
        raise Exception("SIGPIPE could not be set to SIG_DLF")

def getSigName(num):
    "get name for a signal number"
    # find name in signal namespace
    for key in signal.__dict__.iterkeys():
        if (signal.__dict__[key] == num) and key.startswith("SIG") and (key.find("_") < 0):
            return key
    return "signal"+str(num)

# FIXME: how to include stderr from Proc    
class ProcException(Exception):
    "process error exception"
    def __init__(self, desc, returncode, stderr=None):
        self.returncode = returncode
        self.stderr = stderr
        if (returncode < 0):
            # FIXME: translate to string
            msg = "process signaled: " + str(-returncode)
        else:
            msg = "process exited " + str(returncode)
        msg += ": " + desc
        if (stderr != None) and (len(stderr) != 0):
            msg += ":\n" + stderr
        Exception.__init__(self, msg)

class Proc(subprocess.Popen):
    """A process in the pipeline.  This extends subprocess.Popen(),
    it also has the following members:

    cmd - command argument vector
    """

    def __init__(self, pl, cmd, stdin, stdout, stderr):
        self.pipeline = pl
        self.exception = None  # failure exception

        # clone list, converting words to strings
        self.cmd = [str(w) for w in cmd]

        # open files if needed
        (sin, sout, serr) = (stdin, stdout, stderr)
        if isinstance(stdin, str):
            sin = open(sin)
        if isinstance(stdout, str):
            sout = open(sout, "w")
        if isinstance(stderr, str):
            serr = open(serr, "w")

        # need close_fds, or write pipe line fails due to pipes being
        # incorrectly left open (FIXME: could handle in pre-exec)
        subprocess.Popen.__init__(self, self.cmd, stdin=sin, stdout=sout, stderr=serr, preexec_fn=setSigPipe, close_fds=True)

        # close files if we opened them
        if isinstance(stdin, str):
            sin.close()
        if isinstance(stdout, str):
            sout.close()
        if isinstance(stderr, str):
            serr.close()

    def getDesc(self):
        """get command as a string to use as a description of the process.
        Single quote white-space containing arguments."""
        strs = []
        for w in self.cmd:
            if strOps.hasSpaces(w):
                strs.append("'" + w + "'")
            else:
                strs.append(w)
        return " ".join(strs)

    def _handleExit(self):
        if not ((self.returncode == 0) or (self.returncode == -signal.SIGPIPE)):
            self.exception = ProcException(self.getDesc(), self.returncode)
            
    def poll(self, noError=False):
        """Check if the process has completed.  Return True if it has, False
        if it hasn't.  If it completed and exited non-zero or signaled, raise
        an exception unless noError is set.  In which case, True is return and
        failed() must be checked to see if it failed"""
        if super(Proc, self).poll() == None:
            return False
        else:
            self._handleExit()
            if (self.exception != None) and (not noError):
                raise self.exception
            else:
                return True

    def wait(self, noError=False):
        """Wait for the process to complete. Generate an exception if it exits
        non-zero or signals. If noError is True, then return True if the
        process succeded, False on a error."""
        super(Proc, self).wait()
        self._handleExit()
        if (self.exception != None):
            if not noError:
                raise self.exception
            else:
                return False
        else:
            return True

    def failed(self):
        "check if process failed, call after poll() or wait()"
        return (self.exception != None)

    def kill(self, sig=signal.SIGTERM):
        "send a signal to the process"
        os.kill(self.pid, sig)
        
class Procline(object):
    """Process pipeline"""
    def __init__(self, cmds, stdin=None, stdout=None, stderr=None):
        """cmds is either a list of arguments for a single process, or a list
        of such lists for a pipeline. If the stdin/out/err arguments are none,
        they are inherited.  If they are strings, they are opened as a file,
        otherwise it should be file-like object or file number. stdin is
        input to the first process, stdout is output to the last process and
        stderr is attached to all processed."""
        self.procs = []
        self.exception = None
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        if isinstance(cmds[0], str):
            cmds = [cmds]  # one-process pipeline
        prevProc = None
        lastCmd = cmds[len(cmds)-1]
        for cmd in cmds:
            prevProc = self._createProc(cmd, prevProc, (cmd==lastCmd), stdin, stdout, stderr)
        
    def _createProc(self, cmd, prevProc, isLastCmd, stdinFirst, stdoutLast, stderr):
        """create one process"""
        if (prevProc == None):
            stdin = stdinFirst  # first process in pipeline
        else:
            stdin = prevProc.stdout
        if (isLastCmd):
            stdout = stdoutLast # last process in pipeline
        else:
            stdout = subprocess.PIPE
        proc = Proc(self, cmd, stdin=stdin, stdout=stdout, stderr=stderr)
        self.procs.append(proc)

        # this isn't handled by subprocess
        if (prevProc != None):
            # close intermediate output pipes
            prevProc.stdout.close()
            prevProc.stdout = None
        return proc
            
    def _getIoDesc(self):
        "generate shell-like string describing I/O redirections"
        desc = ""
        if (self.stdin != None):
            desc += " <" + str(self.stdin)
        if (self.stdout != None) and (self.stderr == self.stdout):
            desc += " >&" + str(self.stdout)
        else:
            if (self.stdout != None):
                desc += " >" + str(self.stdout)
            if (self.stderr != None):
                desc += " 2>" + str(self.stderr)
        return desc

    def getDesc(self):
        """get the pipeline commands as a string to use as a description"""
        strs = []
        for p in self.procs:
            strs.append(p.getDesc())
        return " | ".join(strs) + self._getIoDesc()

    def kill(self, sig=signal.SIGTERM):
        "send a signal all process in the pipeline"
        for p in self.procs:
            p.kill(sig)
        
    def wait(self, noError=False):
        """Wait for the processes to complete. Generate an exception if one
        exits non-zero or signals, unless noError is True, in which case
        return True if the process succeded, False on a error."""

        # wait on processes
        firstFail = None
        for p in self.procs:
            if not p.wait(noError):
                if firstFail == None:
                    firstFail = p

        # handle failures
        if firstFail != None:
            self.exception = firstFail.exception
            if not noError:
                raise self.exception
            else:
                return False
        else:
            return True

class Pipeline(Procline):
    """File-like object to create and manage a pipeline of subprocesses.

    procs - an ordered list of Proc objects that compose the pipeine"""

    def __init__(self, cmds, mode='r', otherEnd=None, pipePath=None):
        """cmds is either a list of arguments for a single process, or
        a list of such lists for a pipeline.  Mode is 'r' for a pipeline
        who's output will be read, or 'w' for a pipeline to that is to
        have data written to it.  If otherEnd is specified, and is a string,
        it is a file to open as stdio file at the other end of the pipeline.
        If it's not a string, it is assumed to be a file object to use for output.
        
        read pipeline ('r'):
          otherEnd --> cmd[0] --> ... --> cmd[n] --> fh
        
        write pipeline ('w')
          fh --> cmd[0] --> ... --> cmd[n] --> otherEnd

        The field fh is the file object used to access the pipeline.
        If pipePath is specified, then a fifo with this path is used
        instead of creating an unnamed pipe.  This is useful if the
        pipeline needs to be passed to another process by name.  The
        fifo is created if it doesn't exist.
        """
        if (mode == "r") and (mode == "w"):
            raise IOError('invalid mode "' + mode + '"')
        self.mode = mode
        self.closed = False
        self.otherEnd = otherEnd
        self.pipePath = pipePath

        (otherFh, closeOther) = self._getOtherFh()
        (ourRdFh, ourWrFh) = self._getOurFh()
        if mode == "r":
            firstIn = otherFh if (otherFh != None) else 0
            lastOut = ourWrFh
        else:
            lastOut = otherFh if (otherFh != None) else 1
            firstIn = ourRdFh
        Procline.__init__(self, cmds, stdin=firstIn, stdout=lastOut)

        # set file obj to or from pipeline
        if mode == "r":
            if (ourRdFh == subprocess.PIPE):
                self.fh = self.procs[len(self.procs)-1].stdout
            else:
                self.fh = ourRdFh
                ourWrFh.close()
        else:
            if (ourWrFh == subprocess.PIPE):
                self.fh = self.procs[0].stdin
            else:
                self.fh = ourWrFh
                ourRdFh.close()
        if closeOther:
            otherFh.close()

    def _getOtherFh(self):
        """get the other end of the pipeline, return (otherFh, closeOther), with otherFh
        being None if the other end was not opened"""
        if self.otherEnd == None:
            otherFh = None
            closeOther = False
        elif isinstance(self.otherEnd, str):
            otherFh = file(self.otherEnd, self.mode)
            closeOther = True
        else:
            otherFh = self.otherEnd
            closeOther = False
        return (otherFh, closeOther)
        
    def _getOurFh(self):
        """get our end of the pipeline, return (rdFh, wrFh),
        with both values PIPE if a subprocess pipe should be used"""
        
        if self.pipePath != None:
            return self._openFifo()
        else:
            return (subprocess.PIPE, subprocess.PIPE)

    def _openFifo(self):
        "open both ends of pipePath, creating if it doesn't exist"
        if os.path.exists(self.pipePath):
            if not stat.S_ISFIFO(os.stat(self.pipePath).st_mode):
                raise Exception("pipePath is not a FIFO: " + self.pipePath)
        else:
            os.mkfifo(self.pipePath, 0600)
        rdFh = fileOps.fifoOpen(self.pipePath, "r")
        wrFh = fileOps.fifoOpen(self.pipePath, "w")
        return (rdFh, wrFh)

    def unlinkPipe(self):
        "unlink pipe fifo, if it exists"
        if self.pipePath == None:
            os.unlink(self.pipePath)
            pipePath = None
        
    def __iter__(self):
        "iter over contents of file"
        return self.fh.__iter__()

    def next(self):
        return self.fh.next()
  
    def flush(self):
        "Flush the internal I/O buffer."
        self.fh.flush()

    def fileno(self):
        "get the integer OS-dependent file handle"
        return self.fh.fileno()
  
    def write(self, str):
        "Write string str to file."
        self.fh.write(str)

    def writeln(self, str):
        "Write string str to file followed by a newline."
        self.fh.write(str)
        self.fh.write("\n")

    def read(self, size=-1):
        return self.fh.read(size)

    def readline(self, size=-1):
        return self.fh.readline(size)

    def readlines(self, size=-1):
        return self.fh.readlines(size)

    def wait(self, noError=False):
        """wait to for processes to complete, generate an exception if one
        exits no-zero, unless noError is True, in which care return the exit
        code of the first process that failed"""

        self.closed = True

        # must close before waits for output pipeline
        if self.mode == 'w':
            self.fh.close()
        try:
            code = Procline.wait(self, noError)
        finally:
            # must close after waits for input pipeline
            if self.mode == 'r':
                self.fh.close()
        return code

    def close(self):
        "wait for process to complete, with an error if it exited non-zero"
        if not self.closed:
            self.wait()
        if self.exception != None:
            raise exception

__all__ = [ProcException.__name__, Proc.__name__, Procline.__name__, Pipeline.__name__]
