# Copyright 2006-2026 Mark Diekhans
import sys
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio import PycbioException
from pycbio.distrib.parasol import BatchStats

# `para check` stdout for a batch with failures.  para writes the running
# commentary ("N jobs in batch", "Checking finished jobs") to STDERR and only
# these key/value lines to stdout, which is what BatchStats is given.
CHECK_FAILED = """crashed: 3
ranOk: 1
failed 4 times: 3
total jobs in batch: 4
total sick machines: 3 failures: 9
"""

CHECK_OK = """ranOk: 4
total jobs in batch: 4
"""

CHECK_RUNNING = """unsubmitted jobs: 2
queued and waiting: 5
running: 3
ranOk: 1
slow (> 100 minutes): 2
hung (> 4320 minutes): 1
total jobs in batch: 11
"""


def _stats(text):
    return BatchStats(text.split("\n"))


def test_succeeded():
    stats = _stats(CHECK_OK)
    assert stats.ranOk == 4
    assert stats.totalJobs == 4
    assert not stats.hasParasolErrs()
    assert stats.succeeded()


def test_sick_machines():
    "total sick machines: %d failures: %d -- two counts on one line"
    stats = _stats(CHECK_FAILED)
    assert stats.sickMachines == 3
    assert stats.sickFailures == 9


def test_failed_count():
    "failed %d times: %d -- the value is the job count, not the retry limit"
    stats = _stats(CHECK_FAILED)
    assert stats.failed == 3


def test_failed_batch():
    stats = _stats(CHECK_FAILED)
    assert stats.crashed == 3
    assert stats.ranOk == 1
    assert stats.totalJobs == 4
    assert not stats.succeeded()      # ranOk != totalJobs
    assert not stats.hasParasolErrs()  # a crashed job is not a parasol error


def test_slow_and_hung():
    "slow / hung carry the minute threshold in the key, the count in the value"
    stats = _stats(CHECK_RUNNING)
    assert stats.slow == 2
    assert stats.hung == 1
    assert stats.unsubmitted == 2
    assert stats.waiting == 5
    assert stats.running == 3
    assert not stats.succeeded()


def test_defaults_zero():
    "every counter is defined even when para did not print its line"
    stats = _stats(CHECK_OK)
    for fld in ("unsubmitted", "subErrors", "queueErrors", "trackingErrors",
                "waiting", "crashed", "running", "paraResultsErrors",
                "slow", "hung", "failed", "sickMachines", "sickFailures"):
        assert getattr(stats, fld) == 0, fld


def test_para_results_error():
    stats = _stats("para.results: file not found.  paraHub can't write to this dir?\n"
                   "total jobs in batch: 4\n")
    assert stats.paraResultsErrors == 1
    assert stats.hasParasolErrs()
    assert not stats.succeeded()


def test_unknown_line_raises():
    "an unrecognized line is an error rather than a silently dropped statistic"
    with pytest.raises(PycbioException) as ex:
        _stats("total jobs in batch: 4\nsomething new: 1 and more: 2\n")
    assert "don't know how to parse" in str(ex.value)
