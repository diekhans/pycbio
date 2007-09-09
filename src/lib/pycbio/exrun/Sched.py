"""
Scheduling of threads to run tasks (normally rules).  Task scheduling is
non-preemptive.  With task running to completion once started.  Since tasks
usually run one external processes at a time, the number of concurent tasks
controls the number of process executing on a host.  A scheduling group is
associated with a host.  While all threads are on the local host, groups are
used for tasks that start threads on remote hosts.  The motivating goal is to
be able to run multiple cluster batches concurently.  This allows rules to
create batches naturally and still maximize the number of jobs running in
parallel.

"""
import threading
from pycbio.sys.Enumeration import Enumeration

groupLocal = "localhost"

class Task(object):
    """A task, which is something to execute."""
    def __init__(self, runFunc, pri):
        self.thread = None
        self.runFunc = runFunc
        self.pri = pri  # smaller is higher
        self.group =  None
        self.running = False
        self.error = None

    def run(self):
        "run the task"
        self.running = True
        try:
            self.runFunc()
        except e:
            self.error = e
        self.running = False

    def __cmp__(self, other):
        "compare by priority"
        return other.pri - self.pri

class Thread(threading.Thread):
    "Thread in a group"
    def __init__(self, group):
        self.group = group
        self.event = threading.Event()

    def run(self):
        "Run loop for thread"
        while not self.group.stop:
            task = self.group.allocTask()
            task.run()
            self.group.finshedTask(task)
            self.event.wait()

class Group(object):
    """Scheduling group, normally associated with a host."""

    def __init__(self, name, maxConcurrent=1):
        self.lock = threading.RLock()
        self.name = name
        self.maxConcurrent = maxConcurrent
        self.runThreads = []
        self.idleThreads = []
        self.runQ = []      # running tasks, with threads
        self.readyQ = []    # task ready to run, sorted by priority
        self.stop = False

    def addTask(self, task):
        "add a task to queue"
        assert(task.group == None)
        with self.lock:
            self.readyQ.append(task)
            task.group = self

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
