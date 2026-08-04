# Copyright 2006-2026 Mark Diekhans
"""tests of per-rule timing reports and the TSV timing log"""
import os
import sys
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.snakemake import timing

# (user, system, children_user, children_system, elapsed); report_timing uses the
# first four, so a batch's CPU is the wrapper's plus its children's
TIMES0 = os.times_result((1.0, 0.5, 0.0, 0.0, 0.0))
TIMES1 = os.times_result((2.0, 1.0, 3.0, 1.5, 0.0))
# user = (2.0 - 1.0) + 3.0 = 4.0, sys = (1.0 - 0.5) + 1.5 = 2.0, cpu = 6.0


@pytest.fixture(autouse=True)
def noTimingLog():
    "each test starts and ends with no timing log set, since it is module state"
    timing.set_timing_log(None)
    yield
    timing.set_timing_log(None)


def _logLines(path):
    with open(path) as fh:
        return fh.read().splitlines()

def testReportToStderrOnly(tmp_path, capsys):
    timing.report_timing("blast_index", 10.0, TIMES0, TIMES1)
    assert capsys.readouterr().err == ("TIMING blast_index  elapsed=10.0s  user=4.0s  "
                                       "sys=2.0s  cpu=6.0s  wait=4.0s\n")
    assert os.listdir(tmp_path) == []

def testLogGetsHeaderThenRows(tmp_path):
    log = tmp_path / "timing.tsv"
    timing.set_timing_log(log)
    assert timing.get_timing_log() == log
    timing.report_timing("blast_index", 10.0, TIMES0, TIMES1)
    timing.report_timing("project", 20.0, TIMES0, TIMES1)
    assert _logLines(log) == [
        "rule\telapsed_s\tuser_s\tsys_s\tcpu_s\twait_s",
        "blast_index\t10.0\t4.0\t2.0\t6.0\t4.0",
        "project\t20.0\t4.0\t2.0\t6.0\t14.0"]

def testLogAppendsAcrossRuns(tmp_path):
    "a second workflow run adds to the log rather than restarting it"
    log = tmp_path / "timing.tsv"
    timing.set_timing_log(log)
    timing.report_timing("blast_index", 10.0, TIMES0, TIMES1)
    timing.set_timing_log(None)
    timing.set_timing_log(log)
    timing.report_timing("blast_index", 11.0, TIMES0, TIMES1)
    assert _logLines(log)[1:] == ["blast_index\t10.0\t4.0\t2.0\t6.0\t4.0",
                                  "blast_index\t11.0\t4.0\t2.0\t6.0\t5.0"]

def testLogDirCreated(tmp_path):
    log = tmp_path / "logs" / "sub" / "timing.tsv"
    timing.set_timing_log(log)
    timing.report_timing("blast_index", 10.0, TIMES0, TIMES1)
    assert os.path.exists(log)

def testTimedRecordsTheRule(tmp_path, capsys):
    log = tmp_path / "timing.tsv"
    timing.set_timing_log(log)
    with timing.timed("blast_index"):
        pass
    assert capsys.readouterr().err.startswith("TIMING blast_index  elapsed=")
    rows = _logLines(log)
    assert len(rows) == 2
    assert rows[1].split("\t")[0] == "blast_index"

def testTimedReportsOnFailure(tmp_path, capsys):
    "a failed rule is still timed, so the log shows what the run spent before dying"
    log = tmp_path / "timing.tsv"
    timing.set_timing_log(log)
    with pytest.raises(ValueError):
        with timing.timed("blast_index"):
            raise ValueError("job failed")
    assert "TIMING blast_index" in capsys.readouterr().err
    assert len(_logLines(log)) == 2
