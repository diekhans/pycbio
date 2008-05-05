"Classes used to implement rules that execute commands and produce files"

import os.path,sys
from pycbio.sys import typeOps,fileOps,strOps
from pycbio.exrun import ExRunException,Verb
from pycbio.exrun.Graph import Production,Rule
from pycbio.sys.Pipeline import Pipeline,Procline

# FIXME: Auto decompression is not supported, as many programs handle reading
# compressed files and the use of the /proc/ files to get pipe paths causes
# file extension issues.

# FIXME: seems like install could be generalized to any rule, Could the make
# CmdRule only need for a supplied list of commands

# FIXME: the number of different get{In,Out} functions is confusing, and can causes
# errors if the wrong one is used

# FIXME: in transMap run compressed data files got corrupted near
# the start of the *file*. very weird, so we hacked this so compression
# is done after the fact, not on the fifo!.

COMPRESS_BUG = True
if COMPRESS_BUG:
    import socket

def getTmpFifo(exrun, path):
    return exrun.getTmpPath("/var/tmp/"+os.path.basename(path), "tmpfifo")

class FileIn(object):
    """Object used to specified an input File as an argument to a command.  Using
    an instance of this object in a command line automatically adds it as a
    requirement.  It also support automatic compression of the file.

    The prefix attribute is used in construction arguments when an
    option-equals is prepended to the file (--in=fname).  The prefix
    can be specified as an option to the constructor, or in a string concatination
    ("--in="+FileIn(f))."""
    __slots__ = ["file", "argPrefix", "autoDecompress"]

    def __init__(self, file, argPrefix=None, autoDecompress=True):
        autoDecompress = False # FIXME: doesn't work
        self.file = file
        self.argPrefix = argPrefix
        self.autoDecompress = autoDecompress

    def __radd__(self, argPrefix):
        "string concatiation operator that sets argPrefix"
        self.argPrefix = argPrefix
        return self

    def __str__(self):
        """return input file argument"""
        if self.argPrefix == None:
            return self.file.getInPath(self.autoDecompress)
        else:
            return self.argPrefix + self.file.getInPath(self.autoDecompress)

class FileOut(object):
    """Object used to specified an output File as an argument to a command.  Using
    an instance of this object in a command line automatically adds it as a
    production.  It also support automatic compression of the file.

    The prefix attribute is used in construction arguments when an
    option-equals is prepended to the file (--out=fname).  The prefix
    can be specified as an option to the constructor, or in a string concatination
    ("--out="+FileOut(f)).
    """
    __slots__ = ["file", "argPrefix", "autoCompress"]

    def __init__(self, file, argPrefix=None, autoCompress=True):
        self.file = file
        self.argPrefix = argPrefix
        self.autoCompress = autoCompress

    def __radd__(self, argPrefix):
        "string concatiation operator that sets argPrefix"
        self.argPrefix = argPrefix
        return self

    def __str__(self):
        """return input file argument"""
        if self.argPrefix == None:
            return self.file.getOutPath(self.autoCompress)
        else:
            return self.argPrefix + self.file.getOutPath(self.autoCompress)

# FIXME: tmp
IFileRef = FileIn
OFileRef = FileOut


class ActiveIn(object):
    "object used to manage an input file while a command is active"

    def __init__(self, exrun, path, outPath, autoDecompress):
        # outPath used if file has not been installed
        self.inPath = path if outPath == None else outPath
        self.pipe = None
        self.fh = None
        if fileOps.isCompressed(path) and autoDecompress:
            self.pipe = Pipeline([fileOps.decompressCmd(path)], "r", otherEnd=self.inPath,
                                     pipePath=getTmpFifo(exrun, self.inPath))

    def open(self):
        """open the output file for writing from the ExRun process"""
        if self.pipe != None:
            return self.pipe
        else:
            self.fh = open(self.inPath, "r")
            return self.fh

    def getInPath(self):
        "get input path to use, either pipe or tmp file"
        return self.pipe.pipePath if self.pipe != None else self.inPath

    def done(self):
        "complete use of file when a command completes.  This does not install newPath"
        if self.fh != None:
            self.fh.close()
            self.fh = None
        if self.pipe != None:
            try:
                self.pipe.wait()
            finally:
                try:
                    self.pipe.unlinkPipe()
                except:
                    pass
            self.pipe = None
            

class ActiveOut(object):
    "object used to manage an output file while a command is active"

    def __init__(self, exrun, path, outPath, autoCompress):
        self.path = path
        self.outPath = outPath
        self.pipe = None
        self.fh = None
        fileOps.ensureFileDir(path)
        if fileOps.isCompressed(path) and autoCompress:
            if COMPRESS_BUG:
                self.pipe = outPath + "." + socket.gethostname() + "." +str(os.getpid())+".uncmp.tmp"
                self.fh = open(self.pipe, "w")
            else:
                self.pipe = Pipeline([fileOps.compressCmd(path)], "w", otherEnd=self.outPath,
                                     pipePath=getTmpFifo(exrun, self.path))
            
    def open(self):
        """open the output file for writing from the ExRun process"""
        if self.pipe != None:
            if COMPRESS_BUG:
                return self.fh
            else:
                return self.pipe
        elif self.fh != None:
            raise ExRunException("output file already opened: " + self.outPath)
        else:
            self.fh = open(self.outPath, "w")
            return self.fh

    def getOutPath(self):
        "get output path to use, either pipe or tmp file"
        if COMPRESS_BUG:
            return self.pipe if self.pipe != None else self.outPath
        else:
            return self.pipe.pipePath if self.pipe != None else self.outPath

    def done(self):
        "complete use of file when a command completes.  This does not install outPath"
        print "DONE: ", self.outPath, self.pipe
        if self.fh != None:
            self.fh.close()
            self.fh = None
        if self.pipe != None:
            if COMPRESS_BUG:
                tmpCmp = self.outPath + "." + socket.gethostname() + "." +str(os.getpid())+".cmp.tmp"
                pl = Procline([fileOps.compressCmd(self.outPath)], stdin=self.pipe, stdout=tmpCmp)
                pl.wait()
                fileOps.atomicInstall(tmpCmp, self.outPath)
                os.unlink(self.pipe)
                self.pipe = None
            else:
                try:
                    self.pipe.wait()
                finally:
                    try:
                        self.pipe.unlinkPipe()
                    except:
                        pass
                    self.pipe = None

class File(Production):
    """Object representing a file production. This handles atomic file
    creation. CmdRule will install productions of this class after the
    commands succesfully complete.  It also handles automatic compression of
    output.  This is the default behavior, unless overridden by specifying the
    autoCompress=False option the output functions. """

    # FIXME:
    ## no locking is currently required.  If a file has not been installed,
    # then is is only accessed in the rule by a single thread.

    def __init__(self, path, realPath):
        "realPath is use to detect files accessed from different paths"
        Production.__init__(self, path)
        self.path = path
        self.realPath = realPath
        self.outPath = None
        self.installed = False
        self.activeOut = None
        self.activeIns = None

    def __str__(self):
        return self.path

    def getTime(self):
        "modification time of file, or -1.0 if it doesn't exist"
        if os.path.exists(self.path):
            return os.path.getmtime(self.path)
        else:
            return -1.0

    def _setupOut(self, autoCompress):
        "setup output file"
        if self.installed:
            raise ExRunException("output file already installed: " + self.path)
        if self.outPath == None:
            fileOps.ensureFileDir(self.path)
            self.outPath = self.exrun.getTmpPath(self.path)
        self.activeOut = ActiveOut(self.exrun, self.path, self.outPath, autoCompress)
        
    def getOutPath(self, autoCompress=True):
        """Get the output name for the file, which is newPath until the rule
        terminates. This will also create the output directory for the file,
        if it does not exist.  One wants to use FileOut() to define
        a command argument.  This should not be used to get the path to a file
        to be opened in the current process, use openOut() instead."""
        self._setupOut(autoCompress)
        return self.activeOut.getOutPath()

    def openOut(self, autoCompress=True):
        """open the output file for writing from the ExRun process"""
        self._setupOut(autoCompress)
        return self.activeOut.open()

    def _setupIn(self, autoDecompress):
        "setup input file"
        if self.activeIns == None:
            self.activeIns = []
        ai = ActiveIn(self.exrun, self.path, self.outPath, autoDecompress)
        self.activeIns.append(ai)
        return ai
        
    def getInPath(self, autoDecompress=True):
        """Get the input path name of the file.  If a new file has been
        defined using getOutPath(), but has not been installed, it's path is
        return, otherwise path is returned.  One wants to use FileIn() to
        define a command argument.  This should not be used to get the path to
        a file to be opened in the ExRun process, use openIn() instead. """
        ai = self._setupIn(autoDecompress)
        return ai.getInPath()

    def openIn(self, autoDecompress=True):
        """open the input file for reading in the current process"""
        ai = self._setupIn(autoDecompress)
        return ai.open()

    def done(self):
        "called when command completes, waits for pipes but doesn't install output"
        print "FILE.DONE",self.path
        if self.activeOut != None:
            print "   FILE.DONE activeOut"
            self.activeOut.done()
            self.activeOut = None
        elif self.activeIns != None:
            print "   FILE.DONE activeIn",len(self.activeIns)
            firstEx = None
            for ai in self.activeIns:
                try:
                    ai.done()
                except Exception, ex:
                    if firstEx == None:
                        firstEx = ex
            self.activeIns = None
            if firstEx != None:
                raise firstEx

    def finishSucceed(self):
        "finish production with atomic install of new output file as actual file"
        self.done()
        if self.installed:
            raise ExRunException("output file already installed: " + self.path)
        if self.outPath == None:
            raise ExRunException("getOutPath() never called for: " + self.path)
        if not os.path.exists(self.outPath):
            raise ExRunException("output file as not created: " + self.outPath)
        fileOps.atomicInstall(self.outPath, self.path)
        self.installed = True
        self.outPath = None

    def finishFail(self):
        """called when rule failed, doesn't install files"""
        self.done()

    def finishRequire(self):
        """Called when the rule that requires this production finishes
        to clean up decompression pipes"""
        self.done()

class Cmd(list):
    """A command in a CmdRule. An instance can either be a simple command,
    which is a list of words, or a command pipe line, which is a list of list
    of words. The stdin,stdout, stderr arguments are used for redirect I/O.
    stdin/out/err can be open files, strings, or File production objects.
    If they are File objects, the atomic file handling methods are used
    to get the path.
    """

    def __init__(self, cmd, stdin=None, stdout=None, stderr=None):
        """The str() function is called on each word when assembling arguments
        to a comand, so arguments do not need to be strings."""
        # copy list(s)
        if not typeOps.isListLike(cmd):
            raise Exception("command must be a list or list of lists")
        if isinstance(cmd[0], str):
            self.append(tuple(cmd))
        else:
            for c in cmd:
                self.append(tuple(c))
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    # FIXME: getDesc* duplicated from pipeline, should be able to remove
    # with delayed start

    def __getCmdDesc(self, cmd):
        """get command description, single quote white-space containing
        arguments."""
        strs = []
        for w in cmd:
            if isinstance(w, str) and strOps.hasSpaces(w):
                strs.append("'" + w + "'")
            else:
                strs.append(str(w))
        return " ".join(strs)

    def __getIoDesc(self):
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

    def __getDesc(self):
        strs = []
        for cmd in self:
            strs.append(self.__getCmdDesc(cmd))
        return " | ".join(strs) + self.__getIoDesc()

    def isPipe(self):
        "determine if this command contains multiple processes"
        return isinstance(self[0], list) or isinstance(self[0], tuple)
        
    def _getInput(self, fspec):
        """get an input file, if fspec is a File or FileIn object, return getInPath(),
        otherwise str(fspec)"""
        if fspec == None:
            return None
        elif isinstance(fspec, File):
            return fspec.getInPath()
        elif isinstance(fspec, FileIn):
            return fspec.file.getInPath()
        else:
            return str(fspec)

    def _getOutput(self, fspec):
        """get an output file, if fspec is a File or FileOut object, return getOutPath()
        otherwise str(fspec)"""
        if fspec == None:
            return None
        elif isinstance(fspec, File):
            return fspec.getOutPath()
        elif isinstance(fspec, FileOut):
            return fspec.file.getOutPath()
        else:
            return str(fspec)

    def call(self, verb):
        "run command, with tracing"
        if verb.enabled(Verb.trace):
            verb.pr(Verb.trace, self.__getDesc())
        pl = Procline(self, self._getInput(self.stdin), self._getOutput(self.stdout), self._getOutput(self.stderr))
        # FIXME: doesn't print on hang/except; delayed start will allow using
        #  one desc function
        #if verb.enabled(Verb.trace):
        #    verb.pr(Verb.trace, pl.getDesc())
        pl.wait()

class TmpFile(object):
    """Object representing a temporary file that is on a local file system,
    has a unique name and only lasts the life of the life of a CmdRule. A path
    is defined and it is uniquely create when str is called.  If argPrefix is
    specified, it is added before the file name. This allows adding options
    like --foo=filepath.  This can be done automatically with the __radd__
    operator: "--foo="+TmpFile(rule)
    """
    tmpDir = "/scratch/tmp" # FIXME need a better way to get this
    def __init__(self, rule, argPrefix=None, suffix="tmp"):
        self.rule.tmpResources.append(self)
        self.argPrefix = argPrefix
        self.suffix = suffix
        self.path = None

    def __radd__(self, argPrefix):
        "string concatiation operator that sets the argPrefix"
        assert(self.argPrefix == None)
        self.argPrefix = argPrefix
        return self

    def alloc(self):
        "get the file name and setup the path, if it hasn't already been done"
        if self.path == None:
           self.path = fileOps.tmpFileGet(self.prefix, self.suffix)

    def release(self):
        "release tmp file, removing it"
        if (self.path != None) and os.path.exists(self.path):
            os.unlink(self.path)
        self.path == None

    def __str__(self):
        if path == None:
            self.alloc()
        if self.argPrefix == None:
            return self.path
        else:
            return self.argPrefix + self.path

    def __del__(self):
        self.release()

class CmdRule(Rule):
    """Rule to execute processes.  Automatically installs File producions after
    completion.

    This can be used it two ways, either give a lists of commands which are
    executed, or a rule class can be derived from this that executes the
    command when the rule is evaluated.
    
    If commands are specified to the constructor, they are either a Cmd object
    or a list of Cmd objects.  If the input of the Cmd are File objects, they
    are added to the requires, and output of type File are added to the
    produces.  However, if the input of a command is an output of a previous
    command, it the list, it doesn't become a require, to allow outputs to
    also be inputs of other comments for the rule.

    The derived class overrides run() function to evaulate the rule and uses
    the call() function to execute each command or pipeline.

    Rule name is generated from productions if not specified.
    """

    def _mkNamePart(prods):
        if typeOps.isIterable(prods):
            return ",".join(map(str, prods))
        else:
            return str(prods)
    _mkNamePart = staticmethod(_mkNamePart)

    def _mkName(requires, produces):
        return "Rule["+ CmdRule._mkNamePart(requires) + "=>" + CmdRule._mkNamePart(produces)+"]"
    _mkName = staticmethod(_mkName)

    def __init__(self, cmds=None, name=None, requires=None, produces=None):
        requires = typeOps.mkset(requires)
        produces = typeOps.mkset(produces)

        # deal with commands before super init, so all requires and produces
        # are there for the name generation
        self.cmds = None
        if cmds != None:
            self.cmds = []
            if isinstance(cmds, Cmd):
                self._addCmd(cmds, requires, produces)
            else:
                for cmd in cmds:
                    self._addCmd(cmd, requires, produces)
        if name == None:
            name = CmdRule._mkName(requires, produces)
        Rule.__init__(self, name, requires, produces)
        self.tmpResources = []

    def _addCmd(self, cmd, requires, produces):
        assert(isinstance(cmd, Cmd))
        self._addCmdStdio(cmd.stdin, requires, produces)
        self._addCmdStdio(cmd.stdout, produces)
        self._addCmdStdio(cmd.stderr, produces)
        if cmd.isPipe():
            for c in cmd:
                self._addCmdArgFiles(c, requires, produces)
        else:
            self._addCmdArgFiles(c, requires, produces)
        self.cmds.append(cmd)

    def _addCmdStdio(self, fspecs, specSet, exclude=None):
        "add None, a single or a list of file specs as requires or produces links"
        for fspec in typeOps.mkiter(fspecs):
            if  (isinstance(fspec, FileIn) or isinstance(fspec, FileOut)):
                fspec = fspec.file  # get File object for reference
            if (isinstance(fspec, File) and ((exclude == None) or (fspec not in exclude))):
                specSet.add(fspec)

    def _addCmdArgFiles(self, cmd, requires, produces):
        """scan a command's arguments for FileIn and FileOut object and add these to
        requires or produces"""
        for a in cmd:
            if isinstance(a, FileIn):
                requires.add(a.file)
            elif isinstance(a, FileOut):
                produces.add(a.file)
            elif isinstance(a, File):
                raise ExRunException("can't use File object in command argument, use FileIn() or FileOut() to generate a reference object")

    def _callDone(self, file, firstEx):
        "call done function, if exception, set firstEx if it is None"
        try:
            file.done()
        except Exception, ex:
            self.verb.pr(Verb.error, "Exception on file: " + str(file) + ": ", ex, sys.exc_info()[2])
            if firstEx == None:
                firstEx = ex
        return firstEx

    def call(self, cmd):
        "run a command with optional tracing"
        firstEx = None
        try:
            try:
                cmd.call(self.verb)
            except Exception, ex:
                self.verb.pr(Verb.error, "Exception: ", ex, sys.exc_info()[2])
                firstEx = ex
        finally:
            # close compress pipes
            for r in self.requires:
                if isinstance(r, File):
                    firstEx = self._callDone(r, firstEx)
            for p in self.produces:
                if isinstance(p, File):
                    firstEx = self._callDone(p, firstEx)
        if firstEx != None:
            raise firstEx

    def __relTmpResources(self):
        "release any temporary resources"
        for r in self.tmpResources:
            try:
                r.release()
            except:
                self.verb.pr(Verb.error, "releasing tmp resource (ignored): ", ex)
        self.tmpResources.clear()

    def runCmds(self):
        "run commands supplied in the constructor"
        if self.cmds == None:
            raise ExRunException("no commands specified and run() not overridden for CmdRule: " + self.name)
        for cmd in self.cmds:
            self.call(cmd)

    def run(self):
        """run the commands for the rule, the default version runs the
        commands specified at construction, override this for a derived class"""
        self.runCmds()

    def execute(self):
        "execute the rule"
        self.verb.enter()
        try:
            self.run()
        except Exception, ex:
            self.verb.pr(Verb.error, "Exception: ", ex, sys.exc_info()[2])
            raise
        finally:
            self.verb.leave()
