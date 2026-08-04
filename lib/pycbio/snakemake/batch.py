"""Fanning a snakemake stage out over a batch system: a stage's jobs run as one
batch, so snakemake sees one rule rather than thousands of jobs."""
# Copyright 2006-2026 Mark Diekhans

import os
import sys
import shlex
import pipettor
from pycbio import PycbioException
from pycbio.sys import fileOps
from pycbio.snakemake.timing import timed

# The CONTRACT, which is all a batch system has to honour to be usable here:
#
#   1. the stage writes a JOB file -- one shell command line per job;
#   2. the launcher runs them all and BLOCKS until every one has finished;
#   3. it exits non-zero if any job failed, so the rule fails and neither the
#      sentinel nor the declared outputs are taken as complete;
#   4. jobs run with cwd at the workflow root, so command lines can use the same
#      relative paths the Snakefile does.
#
# Per-JOB incrementality is not the launcher's problem: the tools skip work whose
# output already exists, so re-running a batch redoes only what is incomplete.
# That is what lets the whole batch be a black box to snakemake -- one rule, one
# sentinel, thousands of jobs -- instead of thousands of snakemake jobs, each with
# its own scheduling and metadata cost.


class ParasolBatch:
    """UCSC parasol, through pycbio.distrib.parasol.Para, which also handles running
    para over ssh on a head node and parses `para check` into counts.

    parasol runs a job line without a shell: paraNode whitespace-splits it into
    argv (chopLine) and execs that, so `cmd1 && cmd2`, a pipe or a redirect would
    reach cmd1 as arguments rather than being interpreted.  Honouring point 1 of
    the contract -- a job line is a shell command line -- is therefore the
    BatchRunner `prefix` wrapper's job: it must eval the line, as SlurmBatch's
    --wrap does for the line it selects.

    Any existing batch directory is freed first, so para re-creates it from the
    current job list instead of merging with a stale one.  On failure the batch is
    left in place: `para make` reruns only the jobs that failed, so the by-hand
    rerun printed by BatchRunner picks up where this left off.
    """
    name = "parasol"

    def __init__(self, *, para_host=None, cpu=None, mem=None, max_jobs=None,
                 retries=None, batch_suffix=".b1"):
        self.para_host = para_host
        self.cpu = cpu
        self.mem = mem
        self.max_jobs = max_jobs
        self.retries = retries
        self.batch_suffix = batch_suffix

    def batch_dir(self, job_file):
        "the para batch directory, beside the job file: <batch>.b1"
        return os.path.splitext(str(job_file))[0] + self.batch_suffix

    def _para(self, job_file):
        from pycbio.distrib.parasol import Para
        return Para(paraHost=self.para_host, jobFile=str(job_file),
                    paraDir=self.batch_dir(job_file), cpu=self.cpu, mem=self.mem,
                    maxJobs=self.max_jobs, retries=self.retries)

    def run(self, job_file, njobs):
        "para make, blocking; raises if any job failed"
        para = self._para(job_file)
        if para.wasStarted():
            print(f"parasol: freeing existing batch {self.batch_dir(job_file)}",
                  file=sys.stderr)
            para.freeBatch()
            fileOps.rmTree(self.batch_dir(job_file))
            para = self._para(job_file)
        para.make()

    def failure_help(self, job_file, njobs):
        "what to look at, and how to resume -- para reruns only the failed jobs"
        batch = self.batch_dir(job_file)
        return (self._counts(job_file) +
                f"  rerun (only failures redo): para make -batch={batch} {job_file}\n"
                f"  inspect:                    para check -batch={batch}")

    def _counts(self, job_file):
        """`para check` counts, when there is a batch to check.  Guarded on
        wasStarted(): asking about a batch that was never created makes para exit
        non-zero and the runner print its own noisy failure banner, on top of the
        real error we are already reporting."""
        para = self._para(job_file)
        if not para.wasStarted():
            return ""
        try:
            stats = para.check()
        except Exception:
            return ""
        return (f"  {stats.ranOk} ok, {stats.crashed} crashed, "
                f"{stats.running} running, of {stats.totalJobs}\n")


class SlurmBatch:
    """SLURM: the job file as a job ARRAY, one task per line, submitted with
    --wait so the call blocks and its exit status reflects the tasks.

    An array rather than N submissions because the point of this shape is that a
    stage is one scheduler object however many jobs it holds.  `sed -n ${task}p`
    picks the task's command line out of the job file, so the job file stays the
    same artifact parasol uses: readable, re-runnable by hand, and the thing to
    look at when a job fails.

    max_concurrent throttles with the array's `%n`.  log_dir collects per-task
    stdout/stderr, which is where a failed task's output is -- SLURM has no
    equivalent of `para check`, so the logs are the report.
    """
    name = "slurm"

    def __init__(self, log_dir, *, cpus=None, mem=None, time=None, partition=None,
                 account=None, max_concurrent=None, extra=()):
        self.log_dir = str(log_dir)
        self.max_concurrent = max_concurrent
        pairs = (("--cpus-per-task", cpus), ("--mem", mem), ("--time", time),
                 ("--partition", partition), ("--account", account))
        self.flags = [f"{k}={v}" for k, v in pairs if v is not None] + list(extra)

    def batch_dir(self, job_file):
        return None                       # no per-batch state: each run is a new array

    def _array(self, njobs):
        spec = f"1-{njobs}"
        return spec + (f"%{self.max_concurrent}" if self.max_concurrent else "")

    def command(self, job_file, njobs):
        "the sbatch argv; exposed so a workflow can log or dry-run it"
        batch = os.path.splitext(os.path.basename(str(job_file)))[0]
        # the task reads its own line, so the job file stays the source of truth
        wrap = f'eval "$(sed -n ${{SLURM_ARRAY_TASK_ID}}p {shlex.quote(str(job_file))})"'
        return ["sbatch", "--wait", f"--array={self._array(njobs)}",
                f"--job-name={batch}",
                f"--output={self.log_dir}/{batch}-%a.out",
                f"--error={self.log_dir}/{batch}-%a.err",
                *self.flags, f"--wrap={wrap}"]

    def run(self, job_file, njobs):
        "submit the array and block; raises if any task failed"
        fileOps.ensureDir(self.log_dir)
        cmd = self.command(job_file, njobs)
        try:
            pipettor.run(cmd, stdout=1, stderr=2)
        except pipettor.ProcessException as ex:
            raise PycbioException(f"sbatch --wait failed for {job_file} ({njobs} tasks), "
                                  f"see the per-task logs in {self.log_dir}") from ex

    def failure_help(self, job_file, njobs):
        batch = os.path.splitext(os.path.basename(str(job_file)))[0]
        return (f"  per-task output: {self.log_dir}/{batch}-<task>.{{out,err}}\n"
                f"  a task's command is that line of {job_file}\n"
                f"  rerunning the batch is safe: finished work is skipped by the tools")


class BatchRunner:
    """Runs a stage's jobs as one batch on a cluster: the batch system tracks
    per-job state inside the batch, snakemake tracks only whether the stage is
    done.  See the contract above; swap `system` to move between schedulers.

    job_dir    where job files are written (scratch, not a data directory)
    system     ParasolBatch / SlurmBatch, or anything with run(), batch_dir()
               and failure_help()
    prefix     prepended to every command line -- the wrapper that sets the job
               environment up on the compute node -- or None
    timer      context-manager factory taking the batch name, e.g. timing.timed
    """

    def __init__(self, job_dir, system, prefix=None, timer=timed):
        self.job_dir = str(job_dir)
        self.system = system
        self.prefix = prefix
        self.timer = timer

    def job_file(self, batch):
        return os.path.join(self.job_dir, batch + ".jobs")

    def write_jobs(self, batch, cmds):
        "the job file: one command line per job, each through the node wrapper"
        fileOps.ensureDir(self.job_dir)
        path = self.job_file(batch)
        with open(path, "w") as fh:
            for cmd in cmds:
                print(f"{self.prefix} {cmd}" if self.prefix else cmd, file=fh)
        return path

    def run(self, batch, cmds):
        "write the job file and run the batch: blocking, timed, raising on failure"
        job_file = self.write_jobs(batch, cmds)
        with self.timer(batch):
            try:
                self.system.run(job_file, len(cmds))
            except Exception:
                self._report_failure(batch, job_file, len(cmds))
                raise

    def _report_failure(self, batch, job_file, njobs):
        "where to look, before the exception propagates and snakemake fails the rule"
        print(f"{self.system.name}: batch {batch} has failed jobs (see above)",
              file=sys.stderr)
        print(self.system.failure_help(job_file, njobs), file=sys.stderr)

    def run_pending(self, batch, cmds):
        "run a batch, or nothing at all when no item is pending"
        if cmds:
            self.run(batch, cmds)
