"Classes used to implement rules that execute commands and produce files"

import os.path,sys
from pycbio.sys import typeOps,fileOps
from pycbio.exrun import ExRunException,Verb
from pycbio.exrun.Graph import Production,Rule
from pycbio.sys.Pipeline import Pipeline,Procline

# FIXME: Auto decompression is not supported, as many programs handle reading
# compressed files and the use of the /proc/ files to get pipe paths causes
# file extension issues.

# FIXME: seems like install could be generalized to any rule, Could the make
# CmdRule only need for a supplied list of commands

# FIXME: could dynamic properties replace getOut(), etc???

# FIXME: the number of different get{In,Out} functions is confusing, and can causes
# errors if the wrong one is used

class OFileRef(object):
    """

Object used to specified a output file name argument to a command
    that is expanded just before the command is executed."""
    __slots__ = ["file", "prefix", "autoCompress"]

    def __init__(self, file, prefix=None, autoCompress=True):
        self.file = file
        self.prefix = prefix
        self.autoCompress = autoCompress

    def __str__(self):
        """return input file argument"""
        if self.prefix == None:
            return self.file.getOutPath(self.autoCompress)
        else:
            return self.prefix + self.file.getOutPath(self.autoCompress)

    def getOutPath(self):
        "return File.getOutPath() for referenced file"
        return self.file.getOutPath(self.autoCompress)

class IFileRef(object):
    """Object used to specified a input file name argument to a command
    that is expanded just before the command is executed. """
    __slots__ = ["file", "prefix"]

    def __init__(self, file, prefix=None):
        self.file = file
        self.prefix = prefix

    def __str__(self):
        """return input file argument"""
        if self.prefix == None:
            return self.file.getInPath()
        else:
            return self.prefix + self.file.getInPath()

    def getInPath(self):
        "return File.getInPath() for referenced file"
        return self.file.getInPath()

class File(Production):
    """Object representing a file production. This handles atomic file
    creation. CmdRule will install productions of this class after the
    commands succesfully complete.  It also handles automatic compression of
    output.  This is the default behavior, unless overridden by specifying the
    autoCompress=False option the output functions. """

    # no locking is currently required.  If a file has not been installed,
    # then is is only accessed in the rule by a single thread.  Since auto
    # decompressing isn't currently implemented, there is no state to modify
    # once the file has been installed.

    def __init__(self, path, realPath):
        "realPath is use to detect files accessed from different paths"
        Production.__init__(self, path)
        self.path = path
        self.realPath = realPath
        self.newPath = None
        self.installed = False
        self.compPipe = None

    def __str__(self):
        return self.path

    def getTime(self):
        "modification time of file, or -1.0 if it doesn't exist"
        if os.path.exists(self.path):
            return os.path.getmtime(self.path)
        else:
            return -1.0

    def isCompressed(self):
        return self.path.endswith(".gz") or self.path.endswith(".bz2") or self.path.endswith(".Z")

    def getUncompressName(self):
        "get the file name without a .gz/.bz2"
        if self.isCompressed():
            return os.path.splitext(self.path)[0]
        else:
            return self.path

    def getCompressExt(self):
        "return the compressions extension of the file, or an empty string if not compressed"
        if self.isCompressed():
            return os.path.splitext(self.path)[1]
        else:
            return ""

    def _setupOut(self, autoCompress=True):
        "setup output file or pipe"
        if self.installed:
            raise ExRunException("output file already installed: " + self.path)
        if self.newPath == None:
            fileOps.ensureFileDir(self.path)
            self.newPath = self.exrun.getTmpPath(self.path)
        if self.isCompressed() and autoCompress:
            if self.compPipe == None:
                self.compPipe = Pipeline([self.getCompressCmd()], "w", otherEnd=self.newPath,
                                         pipePath = self.exrun.getTmpPath(self.path, "tmpfifo"))
        
    def getOut(self, prefix=None, autoCompress=True):
        """Returns an object that causes the output file path to be substituted
        when str() is call on it.  CmdRule also adds this File as a produces
        when it is in a command specified at construction time.  If prefix is
        specified, it is added before the file name. This allows adding
        options like --foo=filepath.
        """
        return OFileRef(self, prefix, autoCompress)

    def getOutPath(self, autoCompress=True):
        """Get the output name for the file, which is newPath until the rule
        terminates. This will also create the output directory for the file,
        if it does not exist.  Normally one wants to use getOut() to define
        a command argument.  This should not be used to get the path to a file
        to be opened in the current process, use openOut() instead."""
        self._setupOut(autoCompress)
        if self.compPipe != None:
            return self.compPipe.pipePath
        else:
            return self.newPath

    def openOut(self):
        """open the output file for writing from the ExRun process"""
        self._setupOut()
        if self.compPipe != None:
            return self.compPipe
        else:
            return open(self.newPath, "w")

    def _compressWait(self):
        "Wait form compressing process to finish."
        if self.compPipe != None:
            try:
                self.compPipe.wait()
            finally:
                try:
                    self.compPipe.unlinkPipe()
                except:
                    pass
                self.compPipe = None

    def getIn(self, prefix=None):
        """Returns an object that causes the input file path to be substituted
        when str() is call on it.  CmdRule also adds this File as a requires
        when it is in a command specified at construction time.  If prefix is
        specified, it is added before the file name. This allows adding
        options like --foo=filepath.
        """
        return IFileRef(self, prefix)

    def getInPath(self):
        """Get the input path name of the file.  If a new file has been
        defined using getOutPath(), but has not been installed, it's path is
        return, otherwise path is returned.  Normally one wants to use getIn()
        to define a command argument.  This should not be used to get the path
        to a file to be opened in the ExRun process, use openIn() instead. """
        if self.compPipe != None:
            self._compressWait()  # wait for initial compress
        if self.newPath != None:
            return self.newPath
        else:
            return self.path

    def openIn(self):
        """open the input file for reading in the current process"""
        # FIXME: not implemented
        assert(False)
        
    def getCatCmd(self):
        "return get the command name to use to cat the file, considering compression"
        if self.path.endswith(".Z") or self.path.endswith(".gz"):
            return "zcat"
        elif self.path.endswith(".bz2"):
            return "bzcat"
        else:
            return "cat"

    def getCompressCmd(self):
        "return get the command compress the file, or None if not compressed"
        if self.path.endswith(".Z"):
            raise ExRunException("writing compress .Z files not supported")
        elif self.path.endswith(".gz"):
            return "gzip"
        elif self.path.endswith(".bz2"):
            return "bzip2"
        else:
            return None

    def finishSucceed(self):
        "finish production with atomic install of new output file as actual file"
        if self.installed:
            raise ExRunException("output file already installed: " + self.path)
        if self.compPipe != None:
            self._compressWait()
        if self.newPath == None:
            raise ExRunException("getOutPath() never called for: " + self.path)
        if not os.path.exists(self.newPath):
            raise ExRunException("output file as not created: " + self.newPath)
        fileOps.atomicInstall(self.newPath, self.path)
        self.installed = True
        self.newPath = None

    def finishFail(self):
        """called when rule failed, waits for pipe completion, but doesn't
        install files"""
        if self.compPipe != None:
            self._compressWait()

    def finishRequire(self):
        """Called when the rule that requires this production finishes
        to clean up decompression pipes"""
        pass  # decompression not implemented

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
        if isinstance(cmd[0], str):
            self.append(tuple(cmd))
        else:
            for c in cmd:
                self.append(tuple(c))
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def isPipe(self):
        "determine if this command contains multiple processes"
        return isinstance(self[0], list) or isinstance(self[0], tuple)
        
    def _getInput(self, fspec):
        "get an input file, if fspec is a file object, return getInPath(), fspec string"
        if fspec == None:
            return None
        elif isinstance(fspec, File) or isinstance(fspec, IFileRef):
            return fspec.getInPath()
        else:
            return str(fspec)

    def _getOutput(self, fspec):
        "get an output file, if fspec is a file object, return getOutPath(), fspec string"
        if fspec == None:
            return None
        elif isinstance(fspec, File) or isinstance(fspec, OFileRef):
            return fspec.getOutPath()
        else:
            return str(fspec)

    def call(self, verb):
        "run command, with tracing"
        pl = Procline(self, self._getInput(self.stdin), self._getOutput(self.stdout), self._getOutput(self.stderr))
        if verb.enabled(Verb.trace):
            verb.pr(Verb.trace, pl.getDesc())
        pl.wait()

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
            if  (isinstance(fspec, IFileRef) or isinstance(fspec, OFileRef)):
                fspec = fspec.file  # get File object for reference
            if (isinstance(fspec, File) and ((exclude == None) or (fspec not in exclude))):
                specSet.add(fspec)

    def _addCmdArgFiles(self, cmd, requires, produces):
        """scan a command's arguments for IFileRef and OFileRef object and add these to
        requires or produces"""
        for a in cmd:
            if isinstance(a, IFileRef):
                requires.add(a.file)
            elif isinstance(a, OFileRef):
                produces.add(a.file)
            elif isinstance(a, File):
                raise ExRunException("can't use File object in command argument, use getIn() or getOut() to generate a reference object")

    def call(self, cmd):
        "run a commands with optional tracing"
        cmd.call(self.verb)

    def runCmds(self):
        "run commands supplied in the constructor"
        if self.cmds == None:
            raise ExRunException("no commands specified and run() not overridden for CmdRule: " + self.name)
        for cmd in self.cmds:
            self.call(cmd)

    def run(self):
        """run the commands for the rule, the default version runs the
        commands specified at construction, overrider this for a derived class"""
        self.runCmds()

    def execute(self):
        "execute the rule"
        self.verb.enter()
        try:
            self.run()
        except Exception, ex:
            self.verb.pr(Verb.error, "Exception: ", ex)
            raise
        finally:
            self.verb.leave()
