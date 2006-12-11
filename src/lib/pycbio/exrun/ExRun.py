"""Experiment running objects"""
import os.path,sys,socket
from pycbio.exrun.Graph import *
from pycbio.sys import typeOps
from pycbio.exrun import ExRunException
from pycbio.exrun.CmdRule import CmdRule, Cmd, File

os.stat_float_times(True) # very, very gross

# FIXME: currently, if a rule has no requires and produces a file, it is always
#        run once.  Maybe time of a node should be the time of it's productions???
# FIXME: should rules automatically be added?
# FIXME: should File *not* be automatically added?
# FIXME: specification of cmd line with File object can be somewhat redundant, but
#        how can one figure out input vs output??
# FIXME: error output is really hard to read, especially when executing a non-existant program
#        just get `OSError: [Errno 2] No such file or directory', not much help
# FIXME: need to improve graph dump
# FIXME: need tracing of what is out of date
# FIXME: Cmd should allow a Cmd as a command in the pipeline, which would
#        allow all redirection in a subcommand (Pipeline enhancement).

class Verb(object):
    "Verbose tracing, bases on a set of flags."
    
    # flag values
    error = intern("error")     # output erors
    trace = intern("trace")     # basic tracing
    details = intern("details") # detailed tracing
    graph = intern("graph")     # dump graph at the start

    def __init__(self, fh=sys.stderr):
        self.fh = fh
        #self.flags = set([Verb.error, Verb.trace, Verb.graph])
        self.flags = set([Verb.error, Verb.trace])
        self.indent = 0

    def enabled(self, flag):
        """determine if tracing is enabled for the specified flag, flag can be either a single flag or a set"""
        if isinstance(flag, set):
            return (flag and self.flags)
        else:
            return (flag in self.flags)

    def _prIndent(self, msg):
        self.fh.write(("%*s" % (2*self.indent, "")))
        for m in msg:
            self.fh.write(str(m))
        self.fh.write("\n")
        self.fh.flush()

    def prall(self, *msg):
        "unconditionall print a message with indentation"
        self._prIndent(msg)

    def pr(self, flag, *msg):
        "print a message with indentation if flag indicates enabled"
        if self.enabled(flag):
            self._prIndent(msg)

    def enter(self, flag=None, *msg):
        "increment indent count, first optionally output a trace message"
        if self.enabled(flag) and (len(msg) > 0):
            self._prIndent(msg)
        self.indent += 1

    def leave(self, flag=None, *msg):
        "decrement indent count, then optionally outputing a trace message "
        self.indent -= 1
        if self.enabled(flag) and (len(msg) > 0):
            self._prIndent(msg)

class ExRun(object):
    "object that defines and runs an experiment"
    def __init__(self):
        self.pending = None  # pending queue
        self.verb = Verb()
        self.graph = Graph()
        self.hostName = socket.gethostname()
        self.uniqIdCnt = 0
        self.files = {}

    def getUniqId(self):
        "get a unique id for generating file names"
        id = self.hostName + "." + str(os.getpid()) + "." + str(self.uniqIdCnt)
        self.uniqIdCnt += 1
        return id

    def getTmpPath(self, path):
        """generate a unique temporary file path from path, the file will be
        in the same directory.  The file extensions will be maintained, to
        allow recognition of file types, etc. """
        return os.path.join(os.path.dirname(path),
                            "tmp." + self.getUniqId() + os.path.basename(path))

    def _addNode(self, node):
        "add a new node"
        self.graph.addNode(node)
        node.exRun = self
        return node

    def getFile(self, path):
        """get a file production, creating if it doesn't exist, if path is already
        an instance of File instead of a string, just return it."""
        if isinstance(path, File):
            return path
        realPath = os.path.realpath(path)
        fprod = self.files.get(realPath)
        if fprod == None:
            fprod = File(path, realPath)
            self._addNode(fprod)
            self.files[realPath] = fprod
        return fprod

    def getFiles(self, paths):
        """like getFile(), only path can be a single path, or a list of paths,
        or a File object, or list of File objects.  Returns a list of File
        objects"""
        files = []
        for p in typeOps.mkiter(paths):
            files.append(self.getFile(p))
        return files

    def getTarget(self, id):
        "get a target production, creating if it doesn't exist"
        n = self._getNode(id, Target)
        if n == None:
            n = self._addNode(Target(id))
        return n

    def addRule(self, rule):
        "add a new rule"
        self._addNode(rule)
        rule.exRun = self
        rule.verb = self.verb

    def addCmd(self, cmd, name=None, requires=None, produces=None, stdin=None, stdout=None, stderr=None):
        """add a command rule with a single command or pipeline, this is a
        shortcut for addRule(CmdRule(Cmd(....),...)"""
        return self.addRule(CmdRule(Cmd(cmd, stdin=stdin, stdout=stdout, stderr=stderr), name=name, requires=requires, produces=produces))

    def _productionCheck(self):
        """check that all productions with exist or have a rule to build them.
        By check this up front, it prevents file from being created as
        side-affects that are not encoded in the graph"""
        noRuleFor = set()
        for node in self.graph.nodes:
            if isinstance(node, Production) and (len(node.requires) == 0) and (node.getTime() < 0.0):
                noRuleFor.add(node)
        if (len(noRuleFor) > 0):
            raise ExRunException("No rule to build production(s): " + ", ".join([str(p) for p in noRuleFor]))
                
    def _preEvalRuleCheck(self, rule):
        "Sanity check before a rule is run"
        for r in rule.requires:
            if r.getTime() < 0.0:
                raise ExRunException("require should have been built:" + str(r))
        
    def _evalRule(self, rule):
        "evaulate a rule"
        assert(isinstance(rule, Rule))
        self.verb.enter(Verb.trace, "eval rule: ", rule)
        isOk = False
        try:
            self._preEvalRuleCheck(rule)
            self.verb.pr(Verb.details, "run: ", rule)
            rule.executed = True  # before actually executing
            rule.execute()
            if rule.isOutdated():
                raise ExRunException("rule didn't update all productions: " + ", ".join([str(p) for p in rule.getOutdated()]))
            isOk = True
        finally:
            if isOk:
                self.verb.leave(Verb.trace, "done rule: ", rule)
            else:
                # FIXME: should also happen on trace?
                self.verb.leave(Verb.error, "fail rule: ", rule)

    def _buildRule(self, rule):
        "recursively build a rule"
        assert(isinstance(rule, Rule))
        for r in rule.requires:
            self._buildProd(r)
        if rule.isOutdated():
            self._evalRule(rule)
            
    def _buildProd(self, prod):
        "recursively build a production"
        assert(isinstance(prod, Production))
        assert(len(prod.requires) <= 1);
        for r in prod.requires:
            self._buildRule(r)
        if prod.getTime() < 0.0:
            if (len(prod.requires) == 0):
                raise ExRunException("No rule to build: " + prod.name)
            else:
                raise ExRunException("Product not built: " + prod.name)

    def _dumpRule(self, rule):
        self.verb.prall("Rule: ", rule.name)
        self.verb.enter()
        pre = "prd: "
        for p in rule.produces:
            self.verb.prall(pre, p.name)
            pre = "     "
        pre = "req: "
        for r in rule.requires:
            self.verb.prall(pre, r.name)
            pre = "     "
        self.verb.leave()
        
    def dumpGraph(self):
        self.verb.prall("graph dump:")
        self.verb.enter()
        for node in self.graph.bfs():
            if isinstance(node, Rule):
                self._dumpRule(node)
        self.verb.leave()

    def run(self):
        "run the experiment"
        if self.verb.enabled(self.verb.graph):
            self.dumpGraph()
        self.graph.check()
        self._productionCheck()
        for entry in self.graph.getEntryNodes():
            if isinstance(entry, Rule):
                self._buildRule(entry)
            else:
                self._buildProd(entry)

__all__ = (Verb.__name__, ExRun.__name__)
