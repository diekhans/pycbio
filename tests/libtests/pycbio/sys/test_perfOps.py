# Copyright 2006-2025 Mark Diekhans
import sys
import time
import io
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.perfOps import RunTime, run_time_to_row_tsv, timer_report_row_tsv


def testRunTimeCurrent():
    rt = RunTime.current()
    assert rt.wall > 0
    assert rt.cpu_user >= 0
    assert rt.cpu_sys >= 0

def testRunTimeSub():
    rt1 = RunTime(10.0, 2.0, 1.0)
    rt2 = RunTime(7.0, 1.5, 0.5)
    diff = rt1 - rt2
    assert diff.wall == 3.0
    assert diff.cpu_user == 0.5
    assert diff.cpu_sys == 0.5

def testRunTimeSubElapsed():
    t1 = RunTime.current()
    time.sleep(0.01)
    t2 = RunTime.current()
    diff = t2 - t1
    assert diff.wall >= 0.01
    assert diff.cpu_user >= 0
    assert diff.cpu_sys >= 0

def testRunTimeToRowTsvMs():
    rt = RunTime(1.0, 0.6, 0.2)
    fh = io.StringIO()
    run_time_to_row_tsv(fh, rt, label="op")
    lines = fh.getvalue().splitlines()
    assert lines[0] == "op\tms\tfrac"
    # wall row: 1.0 sec * 1000 = 1000.00 ms, frac = 1.0/1.0 = 1.0
    assert lines[1] == "wall\t1000.00\t1.0"
    assert lines[2] == "cpu_user\t600.00\t0.6"
    assert lines[3] == "cpu_sys\t200.00\t0.2"
    assert lines[4] == "wait\t200.00\t0.2"

def testRunTimeToRowTsvSeconds():
    rt = RunTime(1.0, 0.6, 0.2)
    fh = io.StringIO()
    run_time_to_row_tsv(fh, rt, label="op", seconds=True)
    lines = fh.getvalue().splitlines()
    assert lines[0] == "op\tsec\tfrac"
    assert lines[1] == "wall\t1.00\t1.0"
    assert lines[2] == "cpu_user\t0.60\t0.6"
    assert lines[3] == "cpu_sys\t0.20\t0.2"
    assert lines[4] == "wait\t0.20\t0.2"

def testRunTimeToRowTsvWaitClampedToZero():
    # cpu > wall should clamp wait to 0
    rt = RunTime(0.5, 0.4, 0.2)  # cpu=0.6 > wall=0.5
    fh = io.StringIO()
    run_time_to_row_tsv(fh, rt, label="op")
    lines = fh.getvalue().splitlines()
    assert lines[4] == "wait\t0.00\t0.0"

def testTimerReportRowTsv(tmp_path):
    out = tmp_path / "perf.tsv"
    with timer_report_row_tsv(str(out), label="test"):
        time.sleep(0.01)
    lines = out.read_text().splitlines()
    assert lines[0] == "test\tms\tfrac"
    assert len(lines) == 5
