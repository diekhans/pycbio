"""Graph (DAG) of productions and rules"""
import os.path
from pycbio.sys import typeOps

class GraphException(Exception):
    pass

class CycleException(GraphException):
    "Exception indicating a cycle has occured"
    def __init__(self, cycle):
        desc = []
        for n in  cycle:
            desc.append("  " + str(n) + " ->")
        GraphException.__init__(self, "cycle detected:\n" + "\n".join(desc))

class Node(object):
    """Base class for node objects (targets and rules)"""
    def __init__(self, id):
        """produces are incoming edges from nodes requiring this node,
        requires are outgoing edges to nodes that this node requires"""
        self.exRun = None  # set when added to ExRun object
        self.id = id
        self.requires = set()  # next
        self.produces = set()  # prev

    def linkRequires(self, requires):
        "can be single nodes, or lists or sets of nodes, reverse links are created"
        if not typeOps.isIterable(requires):
            requires = (requires,)
        for r in requires:
            self.checkRequires(r)
            r.checkProduces(self)
            self.requires.add(r)
            r.produces.add(self)
            
    def linkProduces(self, produces):
        "can be single nodes, or lists or sets of nodes, reverse links are created"
        if not typeOps.isIterable(produces):
            produces = (produces,)
        for p in produces:
            self.checkProduces(p)
            p.checkRequires(self)
            self.produces.add(p)
            p.requires.add(self)

    def getTime(self):
        """Get the time for the objects represented by this node, as a
        floating point number.  If the object do not exist, return -1.0.
        each node class  must implement this function """
        raise GraphException("getTime() not implemented for " + str(type(self)))

    def isOutdated(self):
        """Determine if this node is outdated"""
        t = self.getTime()
        if t < 0.0:
            return True  # doesn't exist
        for r in self.requires:
            if t < r.getTime():
                return True
        return False

    def __str__(self):
        return self.id

class Production(Node):
    """base class for a production, can only have one requires (produced by) link"""
    def __init__(self, id):
        Node.__init__(self, id)

    def _checkLinkType(self, node):
        if not isinstance(node, Rule):
            raise GraphException("Production " + str(self) + " can only be linked to a Rule, attempt to link to: "
                                 + str(node))

    def checkProduces(self, node):
        "check if node can be linked as a produces node"
        self._checkLinkType(node)

    def checkRequires(self, node):
        "check if node can be linked as a requires node"
        self._checkLinkType(node)
        if len(self.requires) > 0:
            raise GraphException("Production " + str(self) + " already linked to it's produces, attempt to add: "
                                 + str(node))
    
class Rule(Node):
    "base class for a rule"
    def __init__(self, id, requires=None, produces=None):
        Node.__init__(self, id)
        self.verb = None # set when added to ExRun object
        
        if requires != None:
            self.linkRequires(requires)
        if produces != None:
            self.linkProduces(produces)

    def _checkLinkType(self, node):
        if not isinstance(node, Production):
            raise GraphException("Rule " + str(self) + " can only be linked to a Production, attempt to link to: "
                                 + str(node))

    def checkProduces(self, node):
        "check if node can be linked as a produces node"
        self._checkLinkType(node)

    def checkRequires(self, node):
        "check if node can be linked as a requires node"
        self._checkLinkType(node)
    
    def execute(self):
        """Execute the rule, must be implemented by derived class"""
        raise GraphException("evaluate() not implemented for " + str(type(self)))
    
    def getTime(self):
        """Get the time for the rule.  If there requires, it is the time of
        the oldest requirement.  If there are no requires, return 0.0.  This
        way, if a produces doesn't exist, it be out-of-date and the rule
        executes, otherwise, the produces is not out-of-date"""
        if len(self.requires) == 0:
            return 0.0
        tMin = None
        for r in self.requires:
            t = r.getTime()
            if t < 0.0:
                return -1.0  # no reason to search more
            if tMin == None:
                tMin = t
            else:
                tMin = min(tMin, t)
        return tMin

class Graph(object):
    """Graph of productions and rules"""
    def __init__(self):
        self.nodes = set() # set of nodes
        self.nodeMap = {} # map of id to node

    def addNode(self, node):
        "add a node to the graph, checking for duplicated ids"
        if node.id in self.nodeMap:
            raise GraphException("node id already in graph: " + node.id);
        self.nodes.add(node)
        self.nodeMap[node.id] = node

    def getEntryNodes(self):
        """Get entry nodes of the graph; that is those having no productions"""
        entries = [n for n in self.nodes if (len(n.produces) == 0)]
        # sorted by ids so that test produce consistent results
        entries.sort(lambda a,b:cmp(a.id,b.id))
        return entries

    def getNodes(self):
        "get all nodes, sorted by id for consistent test results"
        nodes = list(self.nodes)
        nodes.sort(lambda a,b:cmp(a.id,b.id))
        return nodes

    def _inGraphCheck(self, node):
        "check if a node has been added to the graph"
        if not node in self.nodes:
            raise GraphException("node linked to graph, but was not added to graph: " + node.id)

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
            # no entry nodes, either empty or completely connected, pick lowest id node
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
    

__all__ = (GraphException.__name__, CycleException.__name__, Production.__name__, Rule.__name__, Graph.__name__, )
