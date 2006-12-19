"functions operation on processes"

# FIXME: thes should build on pipeline
# also see stderr changes in genbank copy of this file
# FIXME: names are a bit too verbose (callLines instead of callProcLines)

import subprocess

class ProcException(Exception):
    "process error exception"
    def __init__(self, cmd, returncode, stderr=None):
        self.returncode = returncode
        self.stderr = stderr
        if (returncode < 0):
            msg = "process signaled " + str(-returncode)
        else:
            msg = "process error:" + ": \"" + " ".join(cmd) + "\""
            if (stderr != None) and (len(stderr) != 0):
                msg += ": " + stderr
            else:
                msg += ": exit code: " + str(returncode)
        Exception.__init__(self, msg)

def callProc(cmd, keepLastNewLine=False):
    "call a process and return stdout, exception with stderr in message"
    p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    if (p.returncode != 0):
        raise ProcException(cmd, p.returncode, err)
    if (not keepLastNewLine) and (len(out) > 0) and (out[-1] == "\n"):
        out = out[0:-1]
    return out

def callProcLines(cmd):
    "call a process and return stdout, split into a list of lines, exception with stderr in message"
    out = callProc(cmd)
    return out.split("\n")

def _getStdFile(spec, mode):
    if (spec == None) or (type(spec) == int):
        return spec
    if type(spec) == str:
        return file(spec, mode)
    if type(spec) == file:
        if mode == "w":
            spec.flush()
        return spec
    raise Exception("don't know how to deal with stdio file of type " + type(spec))

def runProc(cmd, stdin="/dev/null", stdout=None, stderr=None, noError=False):
    """run a process, with I/O redirection to specified file paths or open
    file objects. None specifies inheriting. If noError is True, then
    the exit code is returned rather than generating an error"""
    p = subprocess.Popen(cmd, stdin=_getStdFile(stdin, "r"), stdout=_getStdFile(stdout, "w"), stderr=_getStdFile(stderr, "w"))
    p.communicate()
    if ((p.returncode != 0) and not noError):
        raise ProcException(cmd, p.returncode)
    return p.returncode

__all__ = (ProcException.__name__, callProc.__name__, callProcLines.__name__, runProc.__name__)
