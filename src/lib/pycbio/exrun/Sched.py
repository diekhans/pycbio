"""Scheduling of threads to run rules."""
import threading

class Task(object):
    """A task, and associated thread if running."""
    def __init__(self, runFunc, pri):
        self.thread = None
        self.runFunc = runFunc
        self.pri = pri  # smaller is higher

    def __cmp__(self, other):
        "compare by priority"
        return other.pri - self.pri

class Sched(object):
    "object that schedules threads to tasks"

    def __init__(self, maxThreads):
        self.lock = threading.RLock()
        self.maxThreads = maxThreads
        self.numThreads = 0 # current number of threads, excluding main
        self.idleQ = [] # idle threads
        self.runQ = []  # running tasks, with threads
        self.readyQ = [] # task ready to run, sorted by priority
        self.doneEvent = threading.Event()
        self.stop = False  # don't schedule more tasks

    def addTask(self, runFunc, pri):
        "add a new task"
        self.lock.acquired()
        self.runQ.append(Task(runFunc, pri))
        self.lock.release()

    def 

    def run(self):
        """run until all tasks are complete or stop is set.  This runs in
        the main thread and handles creating and displaching threads to
        process tasks.  New tasks maybe added by threads.
        """
        self.lock.acquired()
        while (((len(self.readyQ) > 0) or (len(self.runQ) > 0)) and not self.stop:
        self.runQ.sort()
        self.lock.release()
