"Classes used to implement rules that execute commands and produce files"

import os.path
from pycbio.sys import typeOps,fileOps
from pycbio.exrun.ExRun import ExRunException
from pycbio.exrun.Graph import Production,Rule
from pycbio.sys.Pipeline import Procline

class File(Production):
    """Object representing a file production. This also handles atomic file
    creation. CmdRule will install productions of this class after the
    commands succesfully complete."""

    def __init__(self, id, path):
        "id should be realpath()"
        Production.__init__(self, id)
        self.path = path
        self.newPath = None
        self.installed = False

    def __str__(self):
        return self.path

    def getTime(self):
        "modification time of file, or -1.0 if it doesn't exist"
        if os.path.exists(self.path):
            return os.path.getmtime(self.path)
        else:
            return -1.0

    def getInput(self):
        """Get the input name of the file.  If a new file has been defined
        using getOutput, but has not been installed, it's path is return,
        otherwise path is returned.  This allows a newly created file to be
        used by other commands in a rule before it is installed."""
        if self.newPath != None:
            return self.newPath
        else:
            return self.path

    def getOutput(self):
        """Get the output name for the file, which is newPath until the rule
        terminates. This will also create the output directory for the file,
        if it does not exist."""
        if self.installed:
            raise ExRunException("output file already installed: " + self.path)
        if self.newPath == None:
            fileOps.ensureFileDir(self.path)
            self.newPath = self.getUncompressName() + "." + self.exRun.getUniqId() + ".tmp" + self.getCompressExt()
        return self.newPath

    def isCompressed(self):
        return self.path.endswith(".gz") or self.path.endswith(".bz2")

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

    def install(self):
        "atomic install of new output file as actual file"
        if self.installed:
            raise ExRunException("output file already installed: " + self.path)
        if self.newPath == None:
            raise ExRunException("getOutput() never called for: " + self.path)
        if not os.path.exists(self.newPath):
            raise ExRunException("output file as not created: " + self.newPath)
        if os.path.exists(self.path):
            os.unlink(self.path)
        os.rename(self.newPath, self.path)
        self.installed = True
        self.newPath = None

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

    def _getInput(self, fspec):
        "get an input file, if fspec is a file object, return getInput(), fspec string"
        if fspec == None:
            return None
        elif isinstance(fspec, File):
            return fspec.getInput()
        else:
            return str(fspec)

    def _getOutput(self, fspec):
        "get an output file, if fspec is a file object, return getOutput(), fspec string"
        if fspec == None:
            return None
        elif isinstance(fspec, File):
            return fspec.getOutput()
        else:
            return str(fspec)

    def call(self, verb):
        "run command, with tracing"
        pl = Procline(self, self._getInput(self.stdin), self._getOutput(self.stdout), self._getOutput(self.stderr))
        if verb.enabled(verb.trace):
            verb.pr(verb.trace, pl.getDesc())
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

    Rule id is generated from productions.
    """

    def _mkIdPart(prods):
        if typeOps.isIterable(prods):
            return ",".join(map(str, prods))
        else:
            return str(prods)
    _mkIdPart = staticmethod(_mkIdPart)

    def _mkId(requires, produces):
        return "<"+ CmdRule._mkIdPart(requires) + "=>" + CmdRule._mkIdPart(produces)+">"
    _mkId = staticmethod(_mkId)

    def __init__(self, cmds=None, requires=None, produces=None):
        requires = typeOps.mkset(requires)
        produces = typeOps.mkset(produces)

        # deal with commands before super init, so all requires and produces
        # are there for the id generation
        self.cmds = None
        if cmds != None:
            self.cmds = []
            if isinstance(cmds, Cmd):
                self._addCmd(cmds, requires, produces)
            else:
                for cmd in cmds:
                    self._addCmd(cmd, requires, produces)

        Rule.__init__(self, CmdRule._mkId(requires, produces), requires, produces)

    def _addCmd(self, cmd, requires, produces):
        assert(isinstance(cmd, Cmd))
        self._addCmdFileSpecs(cmd.stdin, requires, produces)
        self._addCmdFileSpecs(cmd.stdout, produces)
        self._addCmdFileSpecs(cmd.stderr, produces)
        self.cmds.append(cmd)

    def _addCmdFileSpecs(self, fspecs, specSet, exclude=None):
        "add None, a single or a list of file specs as requires or produces links"
        for fspec in typeOps.mkiter(fspecs):
            if isinstance(fspec, File) and ((exclude == None) or (fspec not in exclude)):
                specSet.add(fspec)

    def call(self, cmd):
        "run a commands with optional tracing"
        cmd.call(self.verb)

    def runCmds(self):
        "run commands supplied in the constructor"
        if self.cmds == None:
            raise ExRunException("no commands specified and run() not overridden for CmdRule: " + id)
        for cmd in self.cmds:
            self.call(cmd)

    def run(self):
        """run the commands for the rule, the default version runs the
        commands specified at construction, overrider this for a derived class"""
        self.runCmds()

    def _installFileProductions(self):
        for p in self.produces:
            if isinstance(p, File):
                p.install()

    def execute(self):
        "execute the rule"
        self.verb.enter()
        try:
            self.run()
            self._installFileProductions()
        finally:
            self.verb.leave()


