# Copyright 2006-2010 Mark Diekhans
    def _dfsFindCycle(self, edges, n):
        "find a cycle with a DFS"
        self.visited.add(n)
        for e in n.requires:
            if e in edges:
                m = e.next
                if m in self.visited:
                    return [e]  # been here
                else:
                    c = self._dfsFindCycle(edges, m)
                    if c != None:
                        c.append(e)
                        return c
        return None

    def _getACycle(self, edges):
        """get an arbitrary cycle from a list of edges known to contain one.
        or more cycles. Returns a list of edges that are connected by nodes"""
        self.visited = set()
        e = edges.pop()  # arbitrary starting edge
        edges.add(e)
        cycle = self._dfsFindCycle(edges, e.next)
        self.visited = None
        if cycle == None:
            raise Exception("BUG: cycle should have been found")
        cycle.reverse()
        return cycle

    def sort(self):
        "topological sort of graph into order of execution"
        edges = self._getEdgeSet()
        # initialize queue to nodes with no incoming edges
        q = [n for n in self.nodes.itervalues() if (len(n.produces) == 0)]
        pending = []
        while len(q) > 0:
            n = q.pop()
            pending.append(n)
            for e in n.requires:
                edges.discard(e)
                m = e.next
                if len(m.produces & edges) == 0:
                    q.append(m)  # all incoming edges of mode visited
        pending.reverse()
        if len(edges) > 0:
            raise CycleException(self._getACycle(edges))
        return pending
