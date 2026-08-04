# Copyright 2006-2026 Mark Diekhans
"""tests of running a stage's jobs as one batch"""
import os
import sys
import stat
import pytest
from contextlib import contextmanager
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio import PycbioException
from pycbio.snakemake.batch import BatchRunner, ParasolBatch, SlurmBatch

CMDS = ("blastn -query a.fa -out a.psl", "blastn -query b.fa -out b.psl")


class FakeBatch:
    "a batch system that records what it was asked to run, and can fail"
    name = "fake"

    def __init__(self, *, fail=False):
        self.fail = fail
        self.runs = []

    def batch_dir(self, job_file):
        return str(job_file) + ".dir"

    def run(self, job_file, njobs):
        self.runs.append((str(job_file), njobs))
        if self.fail:
            raise PycbioException("fake batch: 1 job crashed")

    def failure_help(self, job_file, njobs):
        return f"  look at {job_file}"


@contextmanager
def _recordingTimer(batch, into):
    into.append(batch)
    yield


def _jobLines(path):
    with open(path) as fh:
        return fh.read().splitlines()


###
# BatchRunner
###
def testWriteJobs(tmp_path):
    runner = BatchRunner(tmp_path / "jobs", FakeBatch(), timer=lambda b: _recordingTimer(b, []))
    path = runner.write_jobs("blast", CMDS)
    assert path == str(tmp_path / "jobs" / "blast.jobs")
    assert _jobLines(path) == list(CMDS)

def testWriteJobsWithPrefix(tmp_path):
    "every job line goes through the node wrapper"
    runner = BatchRunner(tmp_path / "jobs", FakeBatch(), prefix="bin/node-wrapper")
    path = runner.write_jobs("blast", CMDS)
    assert _jobLines(path) == ["bin/node-wrapper " + cmd for cmd in CMDS]

def testRunWritesJobsAndBlocks(tmp_path):
    system = FakeBatch()
    timed = []
    runner = BatchRunner(tmp_path / "jobs", system,
                         timer=lambda b: _recordingTimer(b, timed))
    runner.run("blast", CMDS)
    job_file = str(tmp_path / "jobs" / "blast.jobs")
    assert system.runs == [(job_file, 2)]
    assert timed == ["blast"]
    assert _jobLines(job_file) == list(CMDS)

def testRunPendingWithNothingPending(tmp_path):
    "no job file is even written when no item is pending"
    system = FakeBatch()
    runner = BatchRunner(tmp_path / "jobs", system)
    runner.run_pending("blast", [])
    assert system.runs == []
    assert not os.path.exists(tmp_path / "jobs")

def testRunPendingWithWork(tmp_path):
    system = FakeBatch()
    runner = BatchRunner(tmp_path / "jobs", system,
                         timer=lambda b: _recordingTimer(b, []))
    runner.run_pending("blast", CMDS)
    assert system.runs == [(str(tmp_path / "jobs" / "blast.jobs"), 2)]

def testFailureReportsHelpAndRaises(tmp_path, capsys):
    "the rule must fail, and say where to look, so the sentinel is not touched"
    system = FakeBatch(fail=True)
    runner = BatchRunner(tmp_path / "jobs", system,
                         timer=lambda b: _recordingTimer(b, []))
    with pytest.raises(PycbioException, match="1 job crashed"):
        runner.run("blast", CMDS)
    err = capsys.readouterr().err
    assert "fake: batch blast has failed jobs (see above)" in err
    assert f"look at {tmp_path / 'jobs' / 'blast.jobs'}" in err

def testDefaultTimerIsUsed(tmp_path, capsys):
    runner = BatchRunner(tmp_path / "jobs", FakeBatch())
    runner.run("blast", CMDS)
    assert "TIMING blast  elapsed=" in capsys.readouterr().err


###
# SlurmBatch
###
def testSlurmCommand(tmp_path):
    slurm = SlurmBatch(tmp_path / "logs")
    assert slurm.command(tmp_path / "jobs" / "blast.jobs", 3) == [
        "sbatch", "--wait", "--array=1-3", "--job-name=blast",
        f"--output={tmp_path / 'logs'}/blast-%a.out",
        f"--error={tmp_path / 'logs'}/blast-%a.err",
        '--wrap=eval "$(sed -n ${SLURM_ARRAY_TASK_ID}p '
        + str(tmp_path / "jobs" / "blast.jobs") + ')"']

def testSlurmCommandFlags(tmp_path):
    slurm = SlurmBatch(tmp_path / "logs", cpus=4, mem="8G", time="2:00:00",
                       partition="long", account="proj", max_concurrent=20,
                       extra=("--exclusive",))
    cmd = slurm.command("jobs/blast.jobs", 3)
    assert cmd[2] == "--array=1-3%20"
    assert cmd[6:11] == ["--cpus-per-task=4", "--mem=8G", "--time=2:00:00",
                         "--partition=long", "--account=proj"]
    assert cmd[11] == "--exclusive"

def testSlurmNoBatchDir(tmp_path):
    "each run is a new array, so there is no per-batch state to free"
    assert SlurmBatch(tmp_path / "logs").batch_dir("jobs/blast.jobs") is None


def _fakeSbatch(tmp_path, monkeypatch, exit_code):
    "put an sbatch on PATH that records its argv and exits with exit_code"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    sbatch = bin_dir / "sbatch"
    with open(sbatch, "w") as fh:
        fh.write("#!/bin/sh\n"
                 f'echo "$@" >{tmp_path / "sbatch.argv"}\n'
                 f"exit {exit_code}\n")
    os.chmod(sbatch, os.stat(sbatch).st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    return sbatch

def testSlurmRunBlocksAndSucceeds(tmp_path, monkeypatch):
    _fakeSbatch(tmp_path, monkeypatch, 0)
    slurm = SlurmBatch(tmp_path / "logs")
    slurm.run(tmp_path / "jobs" / "blast.jobs", 3)
    assert os.path.isdir(tmp_path / "logs")             # per-task logs land here
    assert "--array=1-3" in open(tmp_path / "sbatch.argv").read()

def testSlurmRunFailureNamesTheLogs(tmp_path, monkeypatch):
    _fakeSbatch(tmp_path, monkeypatch, 1)
    slurm = SlurmBatch(tmp_path / "logs")
    with pytest.raises(PycbioException, match="see the per-task logs"):
        slurm.run(tmp_path / "jobs" / "blast.jobs", 3)


###
# ParasolBatch
###
def testParasolBatchDir(tmp_path):
    para = ParasolBatch()
    assert para.batch_dir("jobs/blast.jobs") == "jobs/blast.b1"

def testParasolBatchDirSuffix(tmp_path):
    para = ParasolBatch(batch_suffix=".b2")
    assert para.batch_dir(tmp_path / "blast.jobs") == str(tmp_path / "blast.b2")
