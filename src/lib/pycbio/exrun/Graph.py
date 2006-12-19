"""Graph (DAG) of productions and rules"""
import os.path
from pycbio.sys import typeOps
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

class Node(object):
    """Base class for node objects (targets and rules)"""
    def __init__(self, name):
        """Produces are incoming edges from nodes requiring this node,
        requires are outgoing edges to nodes that this node requires.
        Name is used in error messages"""
        self.exRun = None  # set when added to ExRun object
        self.name = name
        self.requires = set()  # next
        self.produces = set()  # prev

    def linkRequires(self, requires):
        "can be single nodes, or lists or sets of nodes, reverse links are created"
        for r in typeOps.mkiter(requires):
            self.checkRequires(r)
            r.checkProduces(self)
            self.requires.add(r)
            r.produces.add(self)
            
    def linkProduces(self, produces):
        "can be single nodes, or lists or sets of nodes, reverse links are created"
        for p in typeOps.mkiter(produces):
            self.checkProduces(p)
            p.checkRequires(self)
            self.produces.add(p)
            p.requires.add(self)

    def __str__(self):
        return self.name

class Production(Node):
    """base class for a production, can only have one requires (produced by) link"""
    def __init__(self, name):
        Node.__init__(self, name)

    def _checkLinkType(self, node):
        if not isinstance(node, Rule):
            raise ExRunException("Production " + str(self) + " can only be linked to a Rule, attempt to link to: " + str(node))

    def checkProduces(self, node):
        "check if node can be linked as a produces node"
        self._checkLinkType(node)

    def checkRequires(self, node):
        "check if node can be linked as a requires node"
        self._checkLinkType(node)
        if len(self.requires) > 0:
            raise ExRunException("Production " + str(self) + " already linked to it's produces, attempt to add: " + str(node))

    def getTime(self):
        """Get the modification time of this Production as a floating point number.
        If the object do not exist, return -1.0.  This is not recurisve, it is
        simply the time associated with the production"""
        raise ExRunException("getTime() not implemented for Production " + str(type(self)))
    
class Rule(Node):
    "base class for a rule"
    def __init__(self, name, requires=None, produces=None):
        Node.__init__(self, name)
        self.executed = False
        self.verb = None # set when added to ExRun object
        if requires != None:
            self.linkRequires(requires)
        if produces != None:
            self.linkProduces(produces)

    def _checkLinkType(self, node):
        if not isinstance(node, Production):
            raise ExRunException("Rule " + str(self) + " can only be linked to a Production, attempt to link to: " + str(node))

    def checkProduces(self, node):
        "check if node can be linked as a produces node"
        self._checkLinkType(node)

    def checkRequires(self, node):
        "check if node can be linked as a requires node"
        self._checkLinkType(node)
    
    def execute(self):
        """Execute the rule, must be implemented by derived class"""
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
        
class Graph(object):
    """Graph of productions and rules"""
    def __init__(self):
        self.nodes = set() # set of nodes

    def addNode(self, node):
        "add a node to the graph"
        self.nodes.add(node)

    def getEntryNodes(self):
        """Get entry nodes of the graph; that is those having no productions"""
        entries = [n for n in self.nodes if (len(n.produces) == 0)]
        # sorted by names so that test produce consistent results
        entries.sort(lambda a,b:cmp(a.name,b.name))
        return entries

    def getNodes(self):
        "get all nodes, sorted by name for consistent test results"
        nodes = list(self.nodes)
        nodes.sort(lambda a,b:cmp(a.name,b.name))
        return nodes

    def _inGraphCheck(self, node):
        "check if a node has been added to the graph"
        if not node in self.nodes:
            raise ExRunException("node linked to graph, but was not added to graph: " + node.name)

    def inGraphCheck(self):
        "check that all nodes linked to the graph have been correctly added to the graph"
        for node in self.nodes:
            for r in node.requires:
                self._inGraphCheck(r)
            for p in node.produces:
                self._inGraphCheck(p)
        
    def _cycleCheck(self, visited, node):
        """check for cycles, once a visited node is found, return list of
        nodes in cycle, throwing an exception when returns to start of
        cycle. Also checks that nodes are in node set, which could occur
        in a node was linked to a node in the graph, but not added"""
        if node in visited:
            return [node]  # cycle detected
        visited.add(node)

        for r in node.requires:
            cycle = self._cycleCheck(visited, r)
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

        entries = self.getEntryNodes()
        if len(entries) == 0:
            # no entry nodes, either empty or completely connected, just pick one
            entries = self.getNodes()[0:1]
        for node in entries:
            self._cycleCheck(set(), node)

    def check(self):
        "check the graph for problems"
        self.inGraphCheck()
        self.cycleCheck()

    def bfs(self):
      "BFS generator for graph"
      # initialize queue
      queue = self.getEntryNodes()
      visited = set(queue)
      while len(queue) > 0:
          node = queue.pop()
          yield node
          for r in node.requires:
              if not r in visited:
                  visited.add(r)
                  queue.append(r)
      # if not all nodes were visited, something is linked by not in nodes
      if len(visited) != len(self.nodes):
          self.inGraphCheck()

__all__ = (CycleException.__name__, Production.__name__, Rule.__name__, Graph.__name__, )
