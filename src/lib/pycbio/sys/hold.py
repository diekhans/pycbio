class _ProcDagSort(object):
    "topological sort of ProcDag. if cycle, pending will contain remaining nodes"
    def __init__(self, dag):
        self.dag = dag
        self.pending = set(dag.procs)
        self.sorted = []

        # Initialize queue with in-degree zero nodes
        queue = self.__extractInDegreeZero()
        
        # loop, moving degree-zero nodes to list, via queue
        while len(queue) > 0:
            # move in-degree zero nodes from queue to ordered list
            self.sorted.extend(list(queue))
            queue.clear()

            # Get the entries that are now in-degree zero
            queue = self.__extractInDegreeZero()

    def __getInDegree(self, proc):
        "get current in-degree for proc considering only pending procs"
        d = 0
        for pin in proc.pins:
            inProc = pin.getConnectedProc()
            if inProc in self.pending:
                d += 1
        return d

    def __extractInDegreeZero(self):
        "get in-degree zero pending procs, remove from pending"
        idgz = set()
        for proc in self.pending:
            if self.__getInDegree(proc) == 0:
                idgz.add(proc)
        self.pending -= idgz
        return idgz

; --------------------------------------------------------------------------

    @staticmethod
    def __isStderrPipe(spec):
        "is spec a PInPOut from stderr"
        if not PInPOut.pIsPipe(spec):
            return False
        dev = spec.dev
        if not (PInPOut.pHasProc(dev.pin) and PInPOut.pHasProc(dev.pout)):
            return False
        return (dev.pout.proc.stderr == dev.pout)

    @staticmethod
    def __isArgPipe(spec):
        "is spec a PInPOut from arguments"
        if not PInPOut.pIsPipe(spec):
            return False
        dev = spec.dev
        if not (PInPOut.pHasProc(dev.pin) and PInPOut.pHasProc(dev.pout)):
            return False
        pio2 = dev.pout if (dev.pin == spec) else dev.pin
        proc2 = pio2.proc
        return not ((pio2 == proc2.stdin) or (pio2 == proc2.stdout) or (pio2 == proc2.stderr))

