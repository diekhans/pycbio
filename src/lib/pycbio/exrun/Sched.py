"""Scheduling of threads to run rules.
"""
import threading
from pycbio.sys.Enumeration import Enumeration

State = Enumeration("State", ("idle", "ready", "run"))

groupLocal = "localhost"

class Task(object):
    """A task, which is something to execute."""
    def __init__(self, runFunc, pri):
        self.thread = None
        self.runFunc = runFunc
        self.pri = pri  # smaller is higher
        self.group =  None
        self.state = None
        self.error = None

    def __cmp__(self, other):
        "compare by priority"
        return other.pri - self.pri

class Group(object):
    """Scheduling group, normally associated with a host.  Tasks can move
    between groups."""

    def __init__(self, name, maxConcurrent=1):
        self.lock = threading.RLock()
        self.name = name
        self.maxConcurrent = maxConcurrent
        self.runQ = []      # running tasks, with threads
        self.readyQ = []    # task ready to run, sorted by priority
        self.idleQ = []     # not in runQ or readyQ
        self.done = threading.Event()

    def assocTask(self, task):
        "associate a task"
        assert(task.group == None)
        self.lock.acquired()
        self.readyQ.append(task)
        task.group = self
        ### start here??
        self.lock.release()

    def disassocTask(self, task):
        "disassociate a task"
        assert(task.group == self)
        assert(task in self.runQ)
        self.lock.acquired()
        self.runQ.remove(task)
        task.group = None
        self.lock.release()
        


class Sched(object):
    "object that schedules threads to tasks"

    def __init__(self, maxConcurrent):
        self.lock = threading.RLock()
        self.stop = False  # don't schedule more tasks

    def addTask(self, runFunc, pri):
        "add a new task"
        self.lock.acquired()
        self.runQ.append(Task(runFunc, pri))
        self.lock.release()

    def _startTask(self, task):
        pass

    def run(self):
        """run until all tasks are complete or stop is set.  This runs in
        the main thread and handles creating and displaching threads to
        process tasks.  New tasks maybe added by threads.
        """
        self.lock.acquired()
        while (((len(self.readyQ) > 0) or (len(self.runQ) > 0)) and not self.stop:
        self.runQ.sort()
        self.lock.release()
