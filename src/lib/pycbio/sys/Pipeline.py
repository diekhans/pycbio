"File-like object to create and manage a pipeline of subprocesses"

# FIXME: NASTY BUG: read gzcat file, stop reading, hangs on wait, because
# close hasn't been done!!   
# FIXME: should use mixins!!
# FIXME: why the seperate Procline class?? (doc why)
# FIXME: should proc throw on failure?
# FIXME: would be nice to have an option to kill off all processes in pipleline
#        if one aborts, but this would require putting them in a process group
#        probably an extra fork

import os, subprocess, signal
from pycbio.sys import strOps

def hasWhiteSpace(word):
    "check if a string contains any whitespace"
    for c in word:
        if c.isspace():
            return True
    return False

class Proc(subprocess.Popen):
    """A process in the pipeline.  This extends subprocess.Popen(),
    it also has the following members:

    cmd - command argument vector
    """

    def __init__(self, pl, cmd, stdin, stdout, stderr):
        self.pipeline = pl
        self.failExcept = None  # failure exception

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
        # incorrectly left open (FIXME: report bug??)
        subprocess.Popen.__init__(self, self.cmd, stdin=sin, stdout=sout, stderr=serr, close_fds=True)

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

    def _saveFailExcept(self):
        self.failExcept = OSError(("process exited with %d: \"%s\" in pipeline \"%s\""
                                   % (self.returncode, self.getDesc(), self.pipeline.getDesc())))

    def poll(self):
        """check if process has completed, return True if it has.  Calle
        failed() to see if it failed."""
        if super(Proc, self).poll() != 0:
            self._saveFailExcept()
            return False
        else:
            return True

    def wait(self):
        """wait for process to complete, set failExcept and return False if
        error occured"""
        if super(Proc, self).wait() != 0:
            self._saveFailExcept()
            return False
        else:
            return True

    def failed(self):
        "check if process failed, call after poll() or wait()"
        return (self.failExcept != None)

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
        self.failExcept = None
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        if isinstance(cmds[0], str):
            cmds = [cmds]  # one-process pipeline
        for cmd in cmds:
            self._createProc(cmd, cmds, stdin, stdout, stderr)
        
    def _createProc(self, cmd, cmds, stdinFirst, stdoutLast, stderr):
        """create one process"""
        if (cmd == cmds[0]):
            stdin = stdinFirst  # first process in pipeline
        else:
            stdin = self.procs[len(self.procs)-1].stdout
        if (cmd == cmds[len(cmds)-1]):
            stdout = stdoutLast # last process in pipeline
        else:
            stdout = subprocess.PIPE
        p = Proc(self, cmd, stdin=stdin, stdout=stdout, stderr=stderr)
        self.procs.append(p)

    def _getIoDesc(self):
        "generate shell-like string describing I/O redirections"
        desc = ""
        if self.stdin != None:
            desc += " <" + str(self.stdin)
        if (self.stdout != None) and (self.stderr == self.stdout):
            desc += " >&" + str(self.stdout)
        else:
            if self.stdout != None:
                desc += " >" + str(self.stdout)
            if self.stderr != None:
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
        """wait to for processes to complete, generate an exception if one exits
        no-zero, unless noError is True, in which care return the exit code of the
        first process that failed"""

        # wait on processes
        firstFail = None
        for p in self.procs:
            if not p.wait():
                if firstFail == None:
                    firstFail = p

        # handle failures
        if firstFail != None:
            self.failExcept = firstFail.failExcept
            if not noError:
                raise self.failExcept
            else:
                return firstFail.returncode
        else:
            return 0

class Pipeline(Procline):
    """File-like object to create and manage a pipeline of subprocesses.

    procs - an ordered list of Proc objects that compose the pipeine"""

    def __init__(self, cmds, mode='r', otherEnd=None):
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
        """
        if (mode == "r") and (mode == "w"):
            raise IOError('invalid mode "' + mode + '"')
        self.mode = mode
        self.closed = False
        self._pipePath = None # created on first call to pipepath

        (firstIn, lastOut, otherFh) = self._setupEnds(otherEnd)
        Procline.__init__(self, cmds, stdin=firstIn, stdout=lastOut)

        # set file obj to or from pipeline
        if mode == "r":
            self.fh = self.procs[len(self.procs)-1].stdout
        else:
            self.fh = self.procs[0].stdin
        if otherFh != None:
            otherFh.close()

    def _setupEnds(self, otherEnd):
        """set files at ends of a pipeline, returns (firstIn, lastOut, otherFh),
        with otherFh being None if a file was not opened for otherEnd, and hence should
        not be closed"""

        # setup other end of pipeline
        otherFhRet = None
        if otherEnd != None:
            if isinstance(otherEnd, str):
                otherFhRet = otherFh = file(otherEnd, self.mode)
            else:
                otherFh = otherEnd
            if self.mode == "r":
                firstIn = otherFh
            else:
                lastOut = otherFh
        else:
            otherFh = None
            if self.mode == "r":
                firstIn = 0
            else:
                lastOut = 1

        # setup this end of pipe
        if self.mode == "r":
            lastOut = subprocess.PIPE
        else:
            firstIn = subprocess.PIPE
        return (firstIn, lastOut, otherFhRet)

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
  
    def pipepath(self):
        """get a file system path for the pipe, which can be passed to another process"""
        if self._pipePath == None:
            self._pipePath = "/proc/" + str(os.getpid()) + "/fd/" + str(self.fh.fileno())
        return self._pipePath
  
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
        if self.failExcept != None:
            raise failExcept
