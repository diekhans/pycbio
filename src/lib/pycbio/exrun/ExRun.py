"""Experiment running objects"""
import os.path,sys,socket
from pycbio.exrun.Graph import *
from pycbio.sys.Pipeline import Procline
from pycbio.sys import strOps,fileOps,typeOps

os.stat_float_times(True) # very, very gross

class ExRunException(Exception):
    pass

class File(Production):
    "object representing a file production"
    def __init__(self, id, path):
        "id should be realpath()"
        Production.__init__(self, id)
        self.path = path
        self.tmpOut = None

    def __str__(self):
        return self.path

    def getTime(self):
        "modification time of file, or -1.0 if it doesn't exist"
        if os.path.exists(self.path):
            return os.path.getmtime(self.path)
        else:
            return -1.0

    def getTmpOut(self):
        "get the temporary output name for the file"
        if self.tmpOut == None:
            self.tmpOut = self.path + "." + self.exRun.getUniqId() + ".tmp"
        return self.tmpOut

    def isCompressed(self):
        return self.path.endswith(".gz")

    def getUncompressed(self):
        "get the file name without a .gz"
        if self.isCompressed():
            return os.path.splitext(self.path)[0]
        else:
            return self.path

    def installTmpOut(self):
        "atomic install of tmp output file as actual file"
        if self.tmpOut == None:
            raise ExRunException("getTmpOut() never called for " + path)
        os.rename(self.tmpOut, self.path)

class Cmd(list):
    """A command in a CmdRule. An instance can either be a simple command,
    which is a list of words, or a command pipe line, which is a list of list
    of words. The stdin,stdout, stderr arguments are used for redirect I/O."""

    def __init__(self, cmd, stdin=None, stdout=None, stderr=None):
        # copy list(s)
        if isinstance(cmd[0], str):
            self.append(tuple(cmd))
        else:
            for c in cmd:
                self.append(tuple(c))
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def _trace(self, verb):
        """trace the command execution, building a description that looks like
        a shell command"""
        desc = []
        for c in self:
            cmdDesc = []
            for w in c:
                if strOps.hasSpaces(w):
                    cmdDesc.append("\"" + w + "\"")
                else:
                    cmdDesc.append(w)
            desc.append(" ".join(cmdDesc))
        desc = " | ".join(desc)
        if self.stdin != None:
            desc += " <" + self.stdin
        if (self.stdout != None) and (self.stderr == self.stdout):
            desc += " >&" + self.stdout
        else:
            if self.stdout != None:
                desc += " >" + self.stdout
            if self.stderr != None:
                desc += " 2>" + self.stderr
        verb.prTrace(1, desc)
        
    def run(self, verb):
        "run the command"
        self._trace(verb)
        pl = Procline(self, self.stdin, self.stdout, self.stderr)
        pl.wait()

class CmdRule(Rule):
    """Rule to execute commands.  The cmds argument can either be a list of
    Cmd objects, a single Cmd object, or a list that is a valid argument to
    Cmd.__init__. If multiple commands are given, they are executed in order.
    Cmds can be added a create or when run() is called"""
    def __init__(self, id, cmds=None, produces=None, requires=None):
        Rule.__init__(self, id, produces, requires)
        self.cmds = []

        # initialize commands
        if cmds != None:
            if isinstance(cmds[0], Cmd):
                for c in cmds:
                    self.addCmd(c)
            else:
                self.addCmd(cmds)

    def addCmd(self, cmd):
        """add a command, or command pipeline.  cmd is either a Cmd object
        or a list that is a valid argument to Cmd.__init__"""
        if isinstance(cmd, Cmd):
            self.cmds.append(cmd)
        else:
            self.cmds.append(Cmd(cmd))

    def mkProdDirs(self):
        "create directories for all file productions"
        for p in self.produces:
            if isinstance(p, File):
                fileOps.ensureFileDir(p.path)

    def run(self):
        "Run the rule, executing the commands"
        self.verb.enter()
        try:
            for cmd in self.cmds:
                cmd.run(self.verb)
        finally:
            self.verb.leave()

class Verb(object):
    "verbose information"

    def __init__(self, fh=sys.stderr):
        self.fh = fh
        self.traceLevel = 1
        self.indent = 0

    def _traceOn(self, level):
        return (self.traceLevel>= level)

    def _prMsg(self, msg):
        self.fh.write(("%*s" % (2*self.indent, "")))
        for m in msg:
            self.fh.write(str(m))
        self.fh.write("\n")

    def prTrace(self, level, *msg):
        "print a trace message"
        if self._traceOn(level):
            self._prMsg(msg)

    def enter(self, level=1, *msg):
        "increment indent count and optionally output a trace message"
        self.indent += 1
        if self._traceOn(level) and (len(msg) > 0):
            self._prMsg(msg)

    def leave(self, level=None, *msg):
        "optionally output a trace message and decrement indent count "
        if self._traceOn(level) and (len(msg) > 0):
            self._prMsg(msg)
        self.indent -= 1

class ExRun(object):
    "object that defines and runs an experiment"
    def __init__(self):
        self.pending = None  # pending queue
        self.verb = Verb()
        self.graph = Graph()
        self.hostName = socket.gethostname()

    def _getNode(self, id, type):
        "great a node of a particular type, or None"
        n = self.graph.nodes.get(id)
        if n != None:
            if not isinstance(n, type):
                raise ExRunException("production " + id + " exists, but is not a " + str(type))
        return n

    def _addNode(self, node):
        "add a new node"
        self.graph.nodes[node.id] = node
        node.exRun = self
        return node

    def getFile(self, path):
        """get a file production, creating if it doesn't exist, if path is already
        an instance of File instead of a string, just return it."""
        if isinstance(path, File):
            return path
        id = os.path.realpath(path)
        n = self._getNode(id, File)
        if n == None:
            n = self._addNode(File(id, path))
        return n

    def getFiles(self, paths):
        """like getFile(), only path can be a single path, or a list of paths,
        or a File object, or list of File objects.  Returns a list of file
        objects"""
        files = []
        if typeOps.isIterable(paths):
            for p in paths:
                files.append(self.getFile(p))
        else:
            files.append(self.getFile(paths))
        return files

    def getTarget(self, id):
        "get a target production, creating if it doesn't exist"
        n = self._getNode(id, Target)
        if n == None:
            n = self._addNode(Target(id))
        return n

    def addRule(self, rule):
        "add a new rule"
        if rule.id in self.graph.nodes:
            raise ExRunException("rule " + id + " conficts with an existing node with the same id");
        n = self._addNode(rule)
        rule.exRun = self
        rule.verb = self.verb
        return n

    def _buildRequires(self, rule):
        "build requirements as needed"
        for r in rule.requires:
            self._buildProd(r.next)

    def _checkProduces(self, rule):
        "check that all produces have been updated"
        for p in rule.produces:
            if p.prev.isOutdated():
                raise ExRunException("product: " + str(p.prev) + " not updated by rule: " + str(rule))
    
    def _evalRule(self, rule):
        "recursively evaulate a rule"
        self.verb.enter(1, "eval rule: ", rule)
        isOk = False
        try:
            self._buildRequires(rule)
            self.verb.prTrace(2, "run: ", rule)
            rule.run()
            self._checkProduces(rule)
            isOk = True
        finally:
            if isOk:
                self.verb.leave(1, "done rule: ", rule)
            else:
                self.verb.leave(0, "failed rule: ", rule)

    def _evalProdRule(self, prod):
        "run rule to build a production"
        self.verb.prTrace(2, "rebuild: ",prod)
        if len(prod.requires) == 0:
            raise ExRunException("no rule to build: " + str(prod))
        for r in prod.requires:
            self._evalRule(r.next)  # will only ever have one
        self.verb.prTrace(2, "rebuilt: ", prod)
        
    def _buildProd(self, prod):
        "recursively rebuild a production if it is out of date"
        assert(isinstance(prod, Production))
        assert(len(prod.requires) <= 1);

        self.verb.enter()
        try:
            if prod.isOutdated():
                self._evalProdRule(prod)
            else:
                self.verb.prTrace(2, "current: ", prod)
        finally:
            self.verb.leave()

    def getUniqId():
        "get a unique id for generating file names"
        return self.hostName + "." + str(os.getpid())

    def run(self):
        "run the experiment"
        self.graph.cycleCheck()

        for entry in self.graph.getEntryNodes():
            if isinstance(entry, Rule):
                raise ExRunException("loose rule: " + str(entry))
            self._buildProd(entry)
