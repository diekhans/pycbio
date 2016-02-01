# Copyright 2006-2012 Mark Diekhans
"""Miscellaneous file operations"""

import os, errno, sys, stat, fcntl, socket, tempfile
import pycbio.sys.procOps

_pipelineMod = None
def _getPipelineClass():
    """To avoid mutual import issues, we get the Pipeline class dynamically on
    first use"""
    global _pipelineMod
    if _pipelineMod is None:
        _pipelineMod = __import__("pycbio.sys.pipeline", fromlist=["pycbio.sys.pipeline"])
    return _pipelineMod.Pipeline

def ensureDir(dir):
    """Ensure that a directory exists, creating it (and parents) if needed."""
    # catching exception rather than checking for existence prevents race condition 
    try: 
        os.makedirs(dir)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise e

def ensureFileDir(fname):
    """Ensure that the directory for a file exists, creating it (and parents) if needed.
    Returns the directory path"""
    dir = os.path.dirname(fname)
    if len(dir) > 0:
        ensureDir(dir)
        return dir
    else:
        return "."

def rmFiles(files):
    """remove one or more files if they exist. files can be a single file
    name of a list of file names"""
    if isinstance(files, str):
        if os.path.exists(files):
            os.unlink(files)
    else:
        for f in files:
            if os.path.exists(f):
                os.unlink(f)

def rmTree(root):
    "remove a file hierarchy, root can be a file or a directory"
    if os.path.isdir(root):
        for dir, subdirs, files in os.walk(root, topdown=False):
            for f in files:
                os.unlink(dir + "/" + f)
            os.rmdir(dir)
    else:
        if os.path.lexists(root):
            os.unlink(root)

def isCompressed(path):
    "determine if a file appears to be compressed by extension"
    return path.endswith(".gz") or path.endswith(".bz2") or path.endswith(".Z")

def compressCmd(path, default="cat"):
    """return the command to compress the path, or default if not compressed, which defaults
    to the `cat' command, so that it just gets written through"""
    if path.endswith(".Z"):
        raise PycbioException("writing compress .Z files not supported")
    elif path.endswith(".gz"):
        return "gzip"
    elif path.endswith(".bz2"):
        return "bzip2"
    else:
        return default

def compressBaseName(path):
    """if a file is compressed, return the path without the compressed extension"""
    if isCompressed(path):
        return os.path.splitext(path)[0]
    else:
        return path

def decompressCmd(path, default="cat"):
    """"return the command to decompress the file to stdout, or default if not compressed, which defaults
    to the `cat' command, so that it just gets written through"""
    if path.endswith(".Z") or path.endswith(".gz"):
        return "zcat"
    elif path.endswith(".bz2"):
        return "bzcat"
    else:
        return default

def opengz(fileName, mode="r"):
    """open a file, if it ends in an extension indicating compression, open
    with a compression or decompression pipe."""
    if isCompressed(fileName):
        if mode == "r":
            cmd = decompressCmd(fileName)
            return _getPipelineClass()([cmd, fileName], mode="r")
        elif mode == "w":
            cmd = compressCmd(fileName)
            return _getPipelineClass()([cmd], mode="w", otherEnd=fileName)
        else:
            raise PycbioException("mode {} not support with compression for {}".format(mode, fileName))
    else:
        return open(fileName, mode)

# FIXME: make these consistent and remove redundant code.  Maybe use
# keyword for flush

def prLine(fh, *objs):
    "write each str(obj) followed by a newline"
    for o in objs:
        fh.write(str(o))
    fh.write("\n")

def prsLine(fh, *objs):
    "write each str(obj), seperated by a space followed by a newline"
    n = 0
    for o in objs:
        if n > 0:
            fh.write(' ')
        fh.write(str(o))
        n += 1
    fh.write("\n")

def prOut(*objs):
    "write each str(obj) to stdout followed by a newline"
    for o in objs:
        sys.stdout.write(str(o))
    sys.stdout.write("\n")

def prErr(*objs):
    "write each str(obj) to stderr followed by a newline"
    for o in objs:
        sys.stderr.write(str(o))
    sys.stderr.write("\n")

def prsOut(*objs):
    "write each str(obj) to stdout, separating with spaces and followed by a newline"
    n = 0
    for o in objs:
        if n > 0:
            sys.stdout.write(' ')
        sys.stdout.write(str(o))
        n += 1
    sys.stdout.write("\n")

def prsfErr(*objs):
    "write each str(obj) to stderr, separating with spaces and followed by a newline and a flush"
    n = 0
    for o in objs:
        if n > 0:
            sys.stderr.write(' ')
        sys.stderr.write(str(o))
        n += 1
    sys.stderr.write("\n")
    sys.stderr.flush()

def prfErr(*objs):
    "write each str(obj) to stderr followed by a newline and a flush"
    for o in objs:
        sys.stderr.write(str(o))
    sys.stderr.write("\n")
    sys.stderr.flush()

def prsOut(*objs):
    "write each str(obj) to stdout, separating with spaces and followed by a newline"
    n = 0
    for o in objs:
        if n > 0:
            sys.stdout.write(' ')
        sys.stdout.write(str(o))
        n += 1
    sys.stdout.write("\n")

def prsErr(*objs):
    "write each str(obj) to stderr, separating with spaces and followed by a newline"
    n = 0
    for o in objs:
        if n > 0:
            sys.stderr.write(' ')
        sys.stderr.write(str(o))
        n += 1
    sys.stderr.write("\n")

def prStrs(fh, *objs):
    "write each str(obj), with no newline"
    for o in objs:
        fh.write(str(o))

def prRow(fh, row):
    """Print a row (list or tupe) to a tab file.
    Does string conversion on each columns"""
    first = True
    for col in row:
        if not first:
            fh.write("\t")
        fh.write(str(col))
        first = False
    fh.write("\n")

def prRowv(fh, *objs):
    """Print a row from each argument to a tab file.
    Does string conversion on each columns"""
    first = True
    for col in objs:
        if not first:
            fh.write("\t")
        fh.write(str(col))
        first = False
    fh.write("\n")

def readFileLines(fname):
    "read lines from a file into a list, removing the newlines"
    fh = opengz(fname)
    lines = []
    for l in fh:
        if l[-1:] == "\n":
            l = l[:-1]
        lines.append(l)
    fh.close()
    return lines

def readLine(fh):
    "read a line from a file, dropping a newline; None on eof"
    l = fh.readline()
    if len(l) == 0:
        return None
    if l[-1:] == "\n":
        l = l[:-1]
    return l

def iterLines(fspec):
    """generator over lines in file, dropping newlines.  If fspec is a string,
    open the file and close at end. Otherwise it is file-like object and will
    not be closed."""
    if isinstance(fspec, str):
        fh = opengz(fspec)
    else:
        fh = fspec
    try:
        for line in fh:
            yield line[:-1]
    finally:
        if isinstance(fspec, str):
            fh.close()

def iterRows(fspec):
    """generator over rows in a tab-separated file.  Each line of the file is
    parsed, split into columns and returned.  If fspec is a string, open the
    file and close at end. Otherwise it is file-like object and will not be
    closed."""
    if isinstance(fspec, str):
        fh = opengz(fspec)
    else:
        fh = fspec
    try:
        for line in fh:
            yield line[0:-1].split("\t")
    finally:
        if isinstance(fspec, str):
            fh.close()

def findTmpDir(tmpDir=None):
    """find the temporary directory to use, if tmpDir is not None, it is use"""
    if tmpDir is not None:
        return tmpDir
    tmpDir = os.getenv("TMPDIR")
    if tmpDir is not None:
        return tmpDir
    # UCSC special checks
    for tmpDir in ("/data/tmp", "/scratch/tmp", "/var/tmp", "/tmp"):
        if os.path.exists(tmpDir):
            return tmpDir
    raise Exception("can't find a tmp directory")

            
def tmpFileGet(prefix=None, suffix="tmp", tmpDir=None):
    """Obtain a tmp file with a unique name. Use tempfile.mkdtemp for
    directories"""
    fh = tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, dir=tmpDir, delete=False)
    fh.close()
    return fh.name

def atomicTmpFile(finalPath):
    "return a tmp file to use with atomicInstall.  This will be in the same directory as finalPath"
    finalPathDir = os.path.dirname(finalPath)
    if finalPathDir == "":
        finalPathDir = '.'
    return tmpFileGet(prefix=os.path.basename(finalPath), suffix="tmp"+os.path.splitext(finalPath)[1], tmpDir=finalPathDir)

def atomicInstall(tmpPath, finalPath):
    "atomic install of tmpPath as finalPath"
    os.rename(tmpPath, finalPath)
    
def uncompressedBase(path):
    "return the file path, removing a compression extension if it exists"
    if path.endswith(".gz") or path.endswith(".bz2") or path.endswith(".Z"):
        return os.path.splitext(path)[0]
    else:
        return path

_devNullFh = None
def getDevNull():
    "get a file object open to /dev/null, caching only one instance"
    global _devNullFh
    if _devNullFh is None:
        _devNullFh = open("/dev/null", "r+")
    return _devNullFh

