"""Miscellaneous file operations"""

import os,os.path,errno,sys,stat
from pycbio.sys.Pipeline import Pipeline

def ensureDir(dir):
    """Ensure that a directory exists, creating it (and parents) if needed."""
    try: 
        os.makedirs(dir)
    except OSError, e:
        if e.errno != errno.EEXIST:
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
    "remove a file hierarchy"
    for dir, subdirs, files in os.walk(root, topdown=False):
        for f in files:
            os.unlink(dir + "/" + f)
        os.rmdir(dir)

def opengz(file, mode="r"):
    """open a file, if it ends in an extension indicating compression, open
    with a decompression pipe.  Only reading is currently supported"""
    ext = os.path.splitext(file)[1]
    if (mode != "r"):
        raise Exception("opengz only supports read access: " + file)
    if (ext == ".gz") or (ext == ".Z") or (ext == ".bz2"):
        open(file).close()  # ensure it exists
        if ext == ".bz2":
            cat = "bzcat"
        else:
            cat = "zcat"
        return Pipeline([cat,file])
    else:
        return open(file, mode)

def prLine(fh, *objs):
    "write each str(obj) followed by a newline"
    for o in objs:
        fh.write(str(o))
    fh.write("\n")

def prOut(*objs):
    "write each str(obj) to stdout followed by a newline"
    for o in objs:
        sys.stdout.write(str(o))
    sys.stdout.write("\n")

def prErr(*objs):
    "write each str(obj) to stdout followed by a newline"
    for o in objs:
        sys.stderr.write(str(o))
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
    fh = file(fname)
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
        cnt = 0
        for line in fh:
            yield line[0:-1]
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
        cnt = 0
        for line in fh:
            cnt += 1
            yield line[0:-1].split("\t")
    finally:
        if isinstance(fspec, str):
            fh.close()

def atomicInstall(tmpPath, finalPath):
    "atomic install of tmpPath as finalPath"
    if os.path.exists(finalPath):
        os.unlink(finalPath)
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
    if _devNullFh == None:
        _devNullFh = open("/dev/null", "r+")
    return _devNullFh
