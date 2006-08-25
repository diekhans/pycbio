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

class Edge(object):
    """Edge between the node objects (productions and rules).
    Since graph is a DAG, previous node is only for debugging purposes"""
    __slots__ = ["prev", "next"]

    def __init__(self, prev, next):
        """create an edge and link it into the graph."""
        # sanity checks
        if not ((isinstance(prev, Production) and isinstance(next, Rule))
                or (isinstance(prev, Rule) and isinstance(next, Production))):
            raise GraphException("can only have edge from Production to Rule or Rule to Production objects, "
                                 + "tried to link " + str(type(prev)) + " to " + str(type(next)) + ": \""
                                 + str(prev) + "\" to \"" + str(next) + "\"")
        if isinstance(prev, Production) and (len(prev.requires) > 0):
            raise GraphException("Production " + str(prev) + " already has an outgoing edge, attempt to add another to: "
                                 + str(next))
        self.prev = prev
        prev.requires.add(self)
        self.next = next
        next.produces.add(self)

class Node(object):
    """base class for node objects (targets and rules)"""
    def __init__(self, id):
        """produces are incoming edges from nodes requiring this node,
        requires are outgoing edges to nodes that this node requires"""
        self.exRun = None  # set when added to ExRun object
        self.id = id
        self.produces = set()
        self.requires = set()

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
            if t < r.next.getTime():
                return True
        return False

    def __str__(self):
        return self.id

class Production(Node):
    """base class for a production, can only have one outgoing edge"""
    def __init__(self, id):
        Node.__init__(self, id)

class Rule(Node):
    "base class for a rule"
    def __init__(self, id, produces=None, requires=None):
        Node.__init__(self, id)
        self.verb = None # set when added to ExRun object
        
        if produces != None:
            self.addProduces(produces)
        if requires != None:
            self.addRequires(requires)

    def addProduces(self, produces):
        "can be single nodes, or lists or sets of nodes, arcs will be created"
        if not typeOps.isIterable(produces):
            self.produces.add(Edge(produces, self))
        else:
            for p in produces:
                self.produces.add(Edge(p, self))

    def addRequires(self, requires):
        "can be single nodes, or lists or sets of nodes, arcs will be created"
        if not typeOps.isIterable(requires):
            self.requires.add(Edge(self, requires))
        else:
            for p in requires:
                self.requires.add(Edge(self, p))

    def run(self):
        """Run the rule, must be implemented by derived class"""
        raise GraphException("run() not implemented for " + str(type(self)))
    
    def getTime(self):
        """Get the time for the rule.  If there requires, it is the time of
        the oldest requirement.  If there are no requires, return 0.0.  This
        way, if a produces doesn't exist, it be out-of-date and the rule
        runs, otherwise, the produes is not out-of-date"""
        if len(self.requires) == 0:
            return 0.0
        tMin = None
        for r in self.requires:
            t = r.next.getTime()
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
        self.nodes = {} # indexed by id

    def getEntryNodes(self):
        """Get entry nodes of the graph; that is those having no products"""
        entries = [n for n in self.nodes.itervalues() if (len(n.produces) == 0)]
        # sorted by ids so that test produce consistent results
        entries.sort(lambda a,b:cmp(a.id,b.id))
        return entries

    def getNodes(self):
        "get all nodes, sorted by id for consitent test results"
        nodes = list(self.nodes.itervalues())
        nodes.sort(lambda a,b:cmp(a.id,b.id))
        return nodes

    def _cycleCheck(self, visited, node):
        """check for cycles, once a visited node is found, return list of
        nodes in cycle, throwing an exception when returns to start of
        cycle"""
        if node in visited:
            return [node]  # cycle detected
        visited.add(node)
        for e in node.requires:
            m  = e.next
            cycle = self._cycleCheck(visited, m)
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
