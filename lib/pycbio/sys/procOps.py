# Copyright 2006-2012 Mark Diekhans
"functions operation on processes"

# FIXME: thes should build on pipeline
# also see stderr changes in genbank copy of this file
# FIXME: names are a bit too verbose (callLines instead of callProcLines)

import os
import re
from pycbio.sys import pipeline


def callProc(cmd, keepLastNewLine=False):
    """call a process and return stdout, exception with stderr in message.
    The  cmd is either a list of command and arguments, or pipeline, specified by
    a list of lists of commands and arguments."""
    stdout = pipeline.DataReader()
    pl = pipeline.Procline(cmd, stdin="/dev/null", stdout=stdout)
    pl.wait()
    out = stdout.get()
    if (not keepLastNewLine) and (len(out) > 0) and (out[-1] == "\n"):
        out = out[0:-1]
    return out


def callProcLines(cmd):
    """call a process and return stdout, split into a list of lines, exception
    with stderr in message."""
    out = callProc(cmd)
    if len(out) == 0:
        return []  # split creates a list of one empty string from an empty string
    return out.split("\n")


def runProc(cmd, stdin="/dev/null", stdout=None, stderr=None):
    """run a process, with I/O redirection to specified file paths or open
    file objects. None specifies inheriting open file."""
    pl = pipeline.Procline(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    pl.wait()


def runProcCode(cmd, stdin="/dev/null", stdout=None, stderr=None):
    """run a process, with I/O redirection to specified file paths or open
    file objects. None specifies inheriting open file.  Return exit code rather
    than raising exception"""
    try:
        pl = pipeline.Procline(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
        pl.wait()
    except pipeline.ProcException as ex:
        if ex.returncode is not None:
            return ex.returncode
        else:
            raise ex
    return 0


def which(prog, makeAbs=False):
    "search PATH for prog, optionally generating an absolute path.  Exception if not found."
    for d in os.environ["PATH"].split(":"):
        if d == "":
            d = "."
        f = d + "/" + prog
        if os.access(f, os.X_OK):
            if (makeAbs):
                return os.path.abspath(f)
            else:
                return f
    raise Exception("Can't find program \"" + prog + "\" on path \"" + os.environ["PATH"] + "\"")

shSafeRe = re.compile("^[-+./_=,:@0-9A-Za-z]+$")


def shQuoteWord(word):
    """quote word so that it will evaluate as a simple string by common Unix
    shells"""
    # help from http://code.activestate.com/recipes/498202/
    word = str(word)
    if shSafeRe.match(word):
        return word
    else:
        return "\\'".join("'" + c + "'" for c in word.split("'"))


def shQuote(words):
    """quote a list of words so that it will evaluate as simple strings by
    common Unix shells"""
    return [shQuoteWord(w) for w in words]


def sshCmd(host, cmd, direct=None):
    ""
    pass

__all__ = (callProc.__name__, callProcLines.__name__, runProc.__name__, which.__name__,
           shQuoteWord.__name__, shQuote.__name__)