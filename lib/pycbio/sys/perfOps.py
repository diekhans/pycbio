# Copyright 2006-2025 Mark Diekhans
"""Performance-related functions"""
import time
import resource
from collections import namedtuple
from contextlib import contextmanager

class RunTime(namedtuple("RunTime",
                         ("wall", "cpu_user", "cpu_sys"))):
    "Run time information"

    @staticmethod
    def current():
        "factory with current times"
        r = resource.getrusage(resource.RUSAGE_SELF)
        return RunTime(time.perf_counter(), r.ru_utime, r.ru_stime)

    def __sub__(self, other):
        return RunTime(self.wall - other.wall,
                       self.cpu_user - other.cpu_user,
                       self.cpu_sys - other.cpu_sys)

def _fmt_row_tsv(fh, label, time, total, in_seconds):
    mult = 1.0 if in_seconds else 1000.0
    print(label, f"{time * mult:.2f}", f"{time / total:.1f}", sep='\t', file=fh)

def run_time_to_row_tsv(fh, run_time, *, label="what", seconds=False):
    """Print, one time per row."""
    unit = "sec" if seconds else "ms"
    print(label, unit, "frac", sep='\t', file=fh)
    cpu = run_time.cpu_user + run_time.cpu_sys
    wall = run_time.wall
    wait = max(wall - cpu, 0)
    _fmt_row_tsv(fh, "wall", wall, wall, seconds)
    _fmt_row_tsv(fh, "cpu_user", run_time.cpu_user, wall, seconds)
    _fmt_row_tsv(fh, "cpu_sys", run_time.cpu_sys, wall, seconds)
    _fmt_row_tsv(fh, "wait", wait, wall, seconds)

@contextmanager
def timer_report_row_tsv(report_tsv="/dev/stdout", *, label="what", seconds=False):
    start_time = RunTime.current()
    yield
    end_time = RunTime.current()
    with open(report_tsv, 'w') as fh:
        run_time_to_row_tsv(fh, end_time - start_time, label=label, seconds=seconds)
