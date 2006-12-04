"""Experiment running objects"""
import os.path,sys,socket
from pycbio.exrun.Graph import *
from pycbio.sys import typeOps

os.stat_float_times(True) # very, very gross

# FIXME: should rules automatically be added

class ExRunException(Exception):
    pass

# FIXME: dependency on file here is weird, have factory in File; must be after ExRunException
from pycbio.exrun.CmdRule import File

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
        "determine if tracing is enabled for the specified flag"
        return (flag in self.flags)

    def _prIndent(self, msg):
        self.fh.write(("%*s" % (2*self.indent, "")))
        for m in msg:
            self.fh.write(str(m))
        self.fh.write("\n")

    def pr(self, flag, *msg):
        "print a message with indentation"
        if self.enabled(flag):
            self._prIndent(msg)

    def enter(self, flag=None, *msg):
        "increment indent count and optionally output a trace message"
        self.indent += 1
        if self.enabled(flag) and (len(msg) > 0):
            self._prIndent(msg)

    def leave(self, flag=None, *msg):
        "optionally output a trace message and decrement indent count "
        if self.enabled(flag) and (len(msg) > 0):
            self._prIndent(msg)
        self.indent -= 1

class ExRun(object):
    "object that defines and runs an experiment"
    def __init__(self):
        self.pending = None  # pending queue
        self.verb = Verb()
        self.graph = Graph()
        self.hostName = socket.gethostname()
        self.uniqIdCnt = 0

    def _getNode(self, id, type):
        "great a node of a particular type, or None"
        n = self.graph.nodeMap.get(id)
        if n != None:
            if not isinstance(n, type):
                raise ExRunException("production " + id + " exists, but is not a " + str(type))
        return n

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
        id = os.path.realpath(path)
        n = self._getNode(id, File)
        if n == None:
            n = self._addNode(File(id, path))
        return n

    def getFiles(self, paths):
        """like getFile(), only path can be a single path, or a list of paths,
        or a File object, or list of File objects.  Returns a list of File
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
        if rule.id in self.graph.nodeMap:
            raise ExRunException("rule " + id + " conficts with an existing node with the same id");
        n = self._addNode(rule)
        rule.exRun = self
        rule.verb = self.verb
        return n

    def _buildRequires(self, rule):
        "build requirements as needed"
        for r in rule.requires:
            self._buildProd(r)

    def _checkProduces(self, rule):
        "check that all produces have been updated"
        for p in rule.produces:
            if p.isOutdated():
                raise ExRunException("product: " + str(p) + " not updated by rule: " + str(rule))
    
    def _evalRule(self, rule):
        "recursively evaulate a rule"
        assert(isinstance(rule, Rule))
        self.verb.enter(Verb.trace, "eval rule: ", rule)
        isOk = False
        try:
            self._buildRequires(rule)
            self.verb.pr(Verb.details, "run: ", rule)
            rule.execute()
            self._checkProduces(rule)
            isOk = True
        finally:
            if isOk:
                self.verb.leave(Verb.trace, "done rule: ", rule)
            else:
                # FIXME: should also happen on trace?
                self.verb.leave(Verb.error, "failed rule: ", rule)

    def _evalProdRule(self, prod):
        "run rule to build a production"
        self.verb.pr(self.verb.details, "build: ",prod)
        if len(prod.requires) == 0:
            raise ExRunException("no rule to build: " + str(prod))
        for r in prod.requires:
            self._evalRule(r)  # will only ever have one
        self.verb.pr(self.verb.details, "built: ", prod)
        
    def _buildProd(self, prod):
        "recursively rebuild a production if it is out of date"
        assert(isinstance(prod, Production))
        assert(len(prod.requires) <= 1);

        self.verb.enter()
        try:
            if prod.isOutdated():
                self._evalProdRule(prod)
            else:
                self.verb.pr(self.verb.details, "current: ", prod)
        finally:
            self.verb.leave()

    def getUniqId(self):
        "get a unique id for generating file names"
        id = self.hostName + "." + str(os.getpid()) + "." + str(self.uniqIdCnt)
        self.uniqIdCnt += 1
        return id

    def dumpGraph(self):
        self.verb.pr(self.verb.graph, "graph dump:")
        self.verb.enter()
        for node in self.graph.bfs():
            if isinstance(node, Rule):
                self.verb.pr(self.verb.graph, "Rule: ", node.id)
            else:
                self.verb.pr(self.verb.graph, "Prod: ", node.id)
        self.verb.leave()
        

    def run(self):
        "run the experiment"
        if self.verb.enabled(self.verb.graph):
            self.dumpGraph()
        self.graph.check()

        for entry in self.graph.getEntryNodes():
            if isinstance(entry, Rule):
                self._evalRule(entry)
            else:
                self._buildProd(entry)

__all__ = (ExRunException.__name__, Verb.__name__, ExRun.__name__)
