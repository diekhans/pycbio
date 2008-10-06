"""Graph (DAG) of productions and rules"""
import os.path
from pycbio.sys import typeOps
from pycbio.sys.Enumeration import Enumeration
from pycbio.exrun import ExRunException

posInf = float("inf")
negInf = float("-inf")

class CycleException(ExRunException):
    "Exception indicating a cycle has occured"
    def __init__(self, cycle):
        desc = []
        for n in  cycle:
            desc.append("  " + str(n) + " ->")
        ExRunException.__init__(self, "cycle detected:\n" + "\n".join(desc))

# state of a rule
RuleState = Enumeration("RuleState",
                        ("new", "running", "success", "failed"))

class Node(object):
    """Base object for all entries in graph. Derived object define generators
    prevNodes() and nextNodes() for traversing tree."""
    def __init__(self, name):
        self.name = name
        # these set when added to ExRun object
        self.exrun = None
        self.verb = None

    def __str__(self):
        return self.name

class Production(Node):
    """Base class for a production. It can only have one requires (produced by)
    link.  When a production is being create by a rule, it is single threaded.
    Once the rule is creating a production has finished, access to it is
    multi-threaded when used as a required."""
    def __init__(self, name):
        Node.__init__(self, name);
        self.producedBy = None
        self.requiredBy = set()

    def nextNodes(self):
        "generator for traversing tree"
        if self.producedBy != None:
            yield self.producedBy

    def prevNodes(self):
        "generator for traversing tree"
        for r in self.requiredBy:
            yield r

    def linkProducedBy(self, producedBy):
        "set producedBy link, and link back to this object"
        if self.producedBy != None:
            raise ExRunException("Production " + str(self) + " producedBy link already set")
        if not isinstance(producedBy, Rule):
            raise ExRunException("Production " + str(self) + " producedBy can only be linked to a Rule, attempt to link to: " + str(producedBy))
        self.producedBy = producedBy
        producedBy.produces.add(self)

    def linkRequiredBy(self, requiredBy):
        """link to rules that require production, can be single rule, lists or
        sets of rules, reverse links are created"""
        for r in typeOps.mkiter(requiredBy):
            if not isinstance(r, Rule):
                raise ExRunException("Production " + str(self) + " requiredBy can only be linked to a Rule, attempt to link to: " + str(r))
            self.requiredBy.add(r)
            r.requires.add(self);

    def finishSucceed(self):
        "called when the rule to create this production finishes successfuly"
        pass

    def finishFail(self):
        "called when the rule to create this production fails"
        pass

    def finishRequire(self):
        """Called when the rule that requires this production finishes. A
        requirement should never be modified, however this is useful for
        cleaning up things like decompress pipelines.  Must be thread-safe."""
        pass

    def getTime(self):
        """Get the modification time of this Production as a floating point number.
        If the object do not exist, return -1.0.  This is not recurisve, it is
        simply the time associated with the production.   Must be thread-safe."""
        raise ExRunException("getTime() not implemented for Production " + str(type(self)))
    
class Rule(Node):
    """Base class for a rule.  A rule is single threaded."""
    def __init__(self, name, requires=None, produces=None):
        Node.__init__(self, name);
        self.state = RuleState.new
        self.requires = set()
        self.produces = set()
        if requires != None:
            self.linkRequires(requires)
        if produces != None:
            self.linkProduces(produces)

    def __str__(self):
        return self.name

    def nextNodes(self):
        "generator for traversing tree"
        for r in self.requires:
            yield r

    def prevNodes(self):
        "generator for traversing tree"
        for p in self.produces:
            yield p

    def linkRequires(self, requires):
        """link in productions required by this node. Can be single nodes, or
        lists or sets of nodes, reverse links are created"""
        for r in typeOps.mkiter(requires):
            if not isinstance(r, Production):
                raise ExRunException("Rule " + str(self) + " requires can only be linked to a Production, attempt to link to: " + str(r))
            r.linkRequiredBy(self)
            
    def linkProduces(self, produces):
        """link in productions produced by this node. Can be single nodes, or
        lists or sets of nodes, reverse links are created"""
        for p in typeOps.mkiter(produces):
            if not isinstance(p, Production):
                raise ExRunException("Rule " + str(self) + " produces can only be linked to a Production, attempt to link to: " + str(p))
            p.linkProducedBy(self)

    def execute(self):
        """Execute the rule, must be implemented by derived class.  ExRun will
        call the approriate finish*() methods on the produces and requires,
        they should not be run by the derived rule class"""
        raise ExRunException("execute() not implemented for " + str(type(self)))
    
    def isOutdated(self):
        """Determine if this rule is outdated and needs to be run.  It is
        outdated if any of the requires are new than any of the produces.  If
        there are no requires, it is outdated if any of the produces don't
        exist.  This is not recursive."""
        # get oldest produces
        pOldest = posInf
        for p in self.produces:
            t = p.getTime()
            if t < 0.0:
                return True  # doesn't exist
            pOldest = min(pOldest, t)

        # compare to requires
        for r in self.requires:
            if pOldest < r.getTime() :
                return True
        return False

    def getOutdated(self):
        """Get list of productions that are out of date relative to requires"""
        outdated = []
        for p in self.produces:
            pt = p.getTime()
            if pt < 0.0:
                outdated.append(p)
            else:
                for r in self.requires:
                    if pt < r.getTime():
                        outdated.append(p)
                        break
        return outdated

    def isOutdated(self):
        """Determine if this rule is outdated and needs to be run.  It is
        outdated if any of the requires are new than any of the produces.  If
        there are no requires, it is outdated if any of the produces don't
        exist.  This is not recursive."""
        # get oldest produces
        pOldest = posInf
        for p in self.produces:
            pt = p.getTime()
            if pt < 0.0:
                return True  # doesn't exist
            pOldest = min(pOldest, pt)

        # compare to requires
        for r in self.requires:
            if pOldest < r.getTime() :
                return True
        return False

class Target(Production):
    """A target is a production that doesn't have any real output, it is just
    and explicty entry point into a graph.  It's time is set to the current
    time when it is run."""

    def __init__(self, name):
        Production.__init__(self, name)
        self.time = -1.0
    
    def getTime(self):
        """Get the time this target's rule completed as a floating point number,
        or -1.0 if it hasn't completed."""
        self.time
        
class Graph(object):
    """Graph of productions and rules.  Once create, the topology of the graph
    is fixed and hence all methods are thread safe.  The contents of nodes
    maye require additional synchronization."""
    def __init__(self):
        self.nodes = set()
        self.productions = set()
        self.rules = set()

    def addNode(self, node):
        "add a node to the graph"
        self.nodes.add(node)
        if isinstance(node, Production):
            self.productions.add(node)
        else:
            self.rules.add(node)

    def getEntryProductions(self):
        """Get entry productions of the graph; that is those having no requireBy"""
        entries = [p for p in self.productions if (len(p.requiredBy) == 0)]
        # sorted by names so that test produce consistent results
        entries.sort(lambda a,b:cmp(a.name,b.name))
        return entries

    def __cycleCheck(self, visited, node):
        """check for cycles, once a visited node is found, return list of
        nodes in cycle, throwing an exception when returns to start of
        cycle. Also checks that nodes are in node set, which could occur
        in a node was linked to a node in the graph, but not added"""
        if node in visited:
            return [node]  # cycle detected
        visited.add(node)

        for n in node.nextNodes():
            cycle = self.__cycleCheck(visited, n)
            if cycle != None:
                if node == cycle[0]:
                    # back at start of cycle
                    cycle.reverse()
                    raise CycleException(cycle)
                else:
                    cycle.append(node)
                    return cycle
        return None

    def cycleCheck(self):
        """check for cycles in graph """
        entries = self.getEntryProductions()
        if len(entries) == 0:
            # no entry nodes, either empty or completely connected, just pick one
            for p in self.productions:
                entries.append(p)
                break
        for node in entries:
            self.__cycleCheck(set(), node)

    def productionCheck(self):
        """check that all productions with exist or have a rule to build them.
        By check this up front, it prevents file from being created as
        side-affects that are not encoded in the graph"""
        noRuleFor = set()
        for prod in self.productions:
            if (prod.producedBy == None) and (prod.getTime() < 0.0):
                noRuleFor.add(prod)
        if (len(noRuleFor) > 0):
            raise ExRunException("No rule to build production(s): " + ", ".join([str(r) for r in noRuleFor]))

    def ruleCheck(self):
        "check that there are no loose rules without productions"
        noProdFor = set()
        for rule in self.rules:
            if len(rule.produces) == 0:
                noProdFor.add(rule)
        if (len(noProdFor) > 0):
            raise ExRunException("Loose rules without production(s): " + ", ".join([str(p) for p in noProdFor]))

    def __inGraphCheck(self, node):
        "check if a node has been added to the graph"
        if not node in self.nodes:
            raise ExRunException("node linked to graph, but was not added to graph: " + node.name)

    def inGraphCheck(self):
        "check that all nodes linked to the graph have been correctly added to the graph"
        for node in self.nodes:
            for n in node.prevNodes():
                self.__inGraphCheck(n)
            for n in node.nextNodes():
                self.__inGraphCheck(n)
        
    def check(self):
        "check graph"
        self.inGraphCheck()
        self.cycleCheck()
        self.productionCheck()
        self.ruleCheck()

    def bfs(self):
      "BFS generator for graph"
      # initialize queue
      queue = self.getEntryProductions()
      visited = set(queue)
      while len(queue) > 0:
          node = queue.pop()
          yield node
          for n in node.nextNodes():
              if not n in visited:
                  visited.add(n)
                  queue.append(n)
      # if not all nodes were visited, something is linked by not in nodes
      if len(visited) != len(self.nodes):
          self.inGraphCheck()

__all__ = (CycleException.__name__, Production.__name__, Rule.__name__, Graph.__name__, "RuleState")
