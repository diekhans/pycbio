"""Per-rule timing for snakemake workflows: elapsed, CPU (user/sys) and wait
time, reported to stderr and appended to a TSV log."""
# Copyright 2006-2026 Mark Diekhans

import os
import sys
import time
from contextlib import contextmanager
from pycbio.sys import fileOps

# The TSV log is the only durable copy: a timing line goes to stderr, i.e. the
# console, and not to snakemake's own .snakemake/log/*.snakemake.log.  A run: block
# executes where snakemake's logging FileHandler is not attached, so its stderr, its
# stdout and even logger.info() are all absent from that file -- only a PARSE-time
# logger.info() reaches it (measured on snakemake 9.23, and confirmed against a real
# run's log: snakemake's own "Finished jobid" is there, none of the TIMING lines are).

TIMING_LOG_COLUMNS = ("rule", "elapsed_s", "user_s", "sys_s", "cpu_s", "wait_s")

_timing_log = None


def set_timing_log(path):
    "where timed() appends its TSV rows; None reports to stderr only"
    global _timing_log
    _timing_log = path


def get_timing_log():
    "the current timing log path, or None"
    return _timing_log


@contextmanager
def timed(rule):
    "bracket a rule's work; print + log elapsed, CPU (user/sys/total), and wait"
    t0, c0 = time.monotonic(), os.times()
    try:
        yield
    finally:
        report_timing(rule, time.monotonic() - t0, c0, os.times())


def report_timing(rule, elapsed, c0, c1):
    "emit one timing line (stderr + the timing log) from before/after os.times()"
    user = (c1.user - c0.user) + (c1.children_user - c0.children_user)
    sysc = (c1.system - c0.system) + (c1.children_system - c0.children_system)
    cpu = user + sysc
    fields = (("elapsed", elapsed), ("user", user), ("sys", sysc),
              ("cpu", cpu), ("wait", elapsed - cpu))
    print("TIMING " + rule + "  " + "  ".join(f"{k}={v:.1f}s" for k, v in fields),
          file=sys.stderr)
    append_timing_log(rule, [v for _, v in fields])


def append_timing_log(rule, values):
    "append a rule's timing row to the TSV timing log (write header if new)"
    if _timing_log is None:
        return
    fileOps.ensureFileDir(_timing_log)
    write_header = not os.path.exists(_timing_log)
    with open(_timing_log, "a") as fh:
        if write_header:
            print("\t".join(TIMING_LOG_COLUMNS), file=fh)
        print(rule + "\t" + "\t".join(f"{v:.1f}" for v in values), file=fh)
