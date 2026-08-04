"""Per-item staleness for snakemake workflows that fan a stage out over a batch
system: which products are missing, and the stamp that makes deciding "nothing to
do" cheap."""
# Copyright 2006-2026 Mark Diekhans

import os
from pathlib import Path
from pycbio.sys import fileOps

# The paradigm this supports, for a workflow that runs one job per ITEM (assembly,
# sample, chromosome) over a batch system:
#
#   * Staleness is per PRODUCT, not per catalog.  A stage declares the products it
#     is missing as its rule outputs, so adding one item builds that item and
#     touching the catalog builds nothing.
#   * A stage's rule also outputs a SENTINEL, which is what orders the stages.
#   * `rule all` must REQUEST every leaf product (all_products()).  Snakemake prunes
#     a job whose outputs exist, and a missing INPUT of a pruned job does not
#     un-prune it -- so depending on the sentinel alone would leave a new item's
#     missing products invisible.
#   * Deciding "nothing to do" must be CHEAP.  Asking the filesystem about
#     every product is O(items x products) stats, paid even when there is
#     nothing to do.  A stamp records a fingerprint of everything the scan's
#     answer depends on; when it still matches and every sentinel exists, the
#     scan is skipped and every stage reports nothing pending.
#
# What the stamp cannot notice, and why that is the right trade: a product deleted
# by hand, or an input re-downloaded in place.  Both are outside the fingerprint, so
# the escape hatch is a full check (full_check=True), and the clean lists that remove
# products must remove the stamp with them.


def _mtime(path):
    "mtime of path, or None when it does not exist"
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def env_flag(name, default="0"):
    "an on/off environment flag, the way a workflow's FULL_CHECK=1 is meant"
    return os.environ.get(name, default) not in ("0", "", "false", "no")


# "The output exists" is the wrong test whenever a stage's inputs can change.  Measured
# consequence, and the reason outputs_current exists: dropping four genes from a GENCODE
# exclusion list restored 1837 projected loci, and a rebuild silently kept the old ones --
# snakemake DID schedule the stage (the exclusion table is a declared input of the rule),
# every one of the 459 jobs then said "already built, skipping", the sentinel was touched,
# and the whole chain was recorded as fresh.  A no-op that reports success is worse than a
# failure.

def outputs_current(outputs, inputs):
    """are all of these outputs present, and none of them older than any of these inputs.

    The oldest output is compared against the newest input, so a stage with several outputs
    is current only if all of them are -- one output rewritten by a partial run does not
    vouch for its siblings.

    A missing input is IGNORED rather than treated as infinitely new.  Some inputs are
    legitimately absent: an assembly with no CenSat annotation is a filter that does not
    apply, not an error, and a tool that tolerates the absence at read time must not
    rebuild forever because of it.  A missing REQUIRED input is the reading code's error
    to raise, with a message about what to run, which it can do far better here.
    """
    outs = [Path(p) for p in outputs]
    if not all(p.exists() for p in outs):
        return False
    ins = [Path(p) for p in inputs]
    newest = max((p.stat().st_mtime for p in ins if p.exists()), default=0.0)
    return min(p.stat().st_mtime for p in outs) >= newest


class ProductScan:
    """Decides, once per workflow parse, whether the per-item product scan can be
    skipped -- and hands out the three product lists each fan-out stage needs.

    items       callable -> the items to process (called only when scanning, so the
                catalog is not even read on the fast path)
    stamp       path of the fingerprint file
    sentinels   every stage's sentinel path.  All of them: one missing from this
                list lets a never-completed stage look finished.
    watch       paths whose mtime joins the fingerprint -- the manually-populated
                input directories.  A NEW per-item subdirectory bumps its parent's
                mtime and so forces a rescan; re-populating one in place does not.
    full_check  force the scan (an env flag in practice)
    log         where to record which mode this run took; a parse-time logger.info
                is the one thing that reaches snakemake's own log file

    Usage in a Snakefile:

        from pycbio.snakemake import ProductScan, env_flag

        scan = ProductScan(items=used, stamp=SCAN_STAMP, sentinels=SENTINELS,
                           watch=DROP_DIRS, full_check=env_flag("FULL_CHECK"),
                           log=logger.info)
        work = scan.pending(blast_index_prods)          # [(item, [missing])]
        rule blast_index:
            output: scan.pending_products(work), touch(SENTINEL)
            run: run_batch("blast_index", [cmd(i) for i, _ in work])
        ...
        scan.record_if_clean()                          # last in the file
    """

    def __init__(self, items, stamp, sentinels, watch=(), full_check=False, log=None):
        self.items = items
        self.stamp = str(stamp)
        self.sentinels = [str(p) for p in sentinels]
        self.watch = [str(p) for p in watch]
        self.full_check = full_check
        self._found_work = False
        self.fingerprint = self._fingerprint()
        self.skip_scan, self.reason = self._mode()
        if log is not None:
            log("per-item scan: {} -- {}".format(
                "SKIPPED (fast path)" if self.skip_scan else "FULL", self.reason))

    # ---- the fast-path decision ----

    def _fingerprint(self):
        "everything the scan's answer depends on, cheaply: the item set + watched mtimes"
        names = sorted(str(item) for item in self.items())
        watched = sorted(f"{p}={_mtime(p)}" for p in self.watch)
        return "\n".join(names + watched) + "\n"

    def _stamp_matches(self):
        try:
            with open(self.stamp) as fh:
                return fh.read() == self.fingerprint
        except OSError:
            return False

    def _mode(self):
        """(skip the scan?, why).  The reason is for the log, so a run records which
        MODE it was in: without it a fast run and a run that genuinely had nothing to
        do are indistinguishable afterwards, and so are a slow run and a real
        problem."""
        if self.full_check:
            return False, "full check requested"
        missing = [p for p in self.sentinels if _mtime(p) is None]
        if missing:
            return False, f"stage sentinel missing ({missing[0]})"
        if not self._stamp_matches():
            return False, ("no scan stamp yet" if _mtime(self.stamp) is None else
                           "item set or a watched input changed since the last scan")
        return True, "scan stamp current"

    # ---- the three product lists ----

    def pending(self, products, items=None):
        """[(item, [its missing products])] for the items with work to do.  A None
        path is not required -- that is how an item that cannot have a product (no
        input for it) is excluded without special-casing the caller.  Nothing is
        pending on the fast path."""
        if self.skip_scan:
            return []
        items = self.items() if items is None else items
        work = [(item, self._missing(products, item)) for item in items]
        pending = [(item, missing) for item, missing in work if missing]
        self._found_work = self._found_work or bool(pending)
        return pending

    @staticmethod
    def _missing(products, item):
        "an item's products that are neither excluded (None) nor already built"
        return [p for p in products(item)
                if p is not None and not os.path.exists(str(p))]

    @staticmethod
    def pending_products(work):
        "the missing paths across pending items -- a stage's real rule outputs"
        return [p for _, missing in work for p in missing]

    def all_products(self, products, items=None):
        """Every product of a stage, present or not, for `rule all` and for a
        downstream rule's inputs.  Dropped on the fast path: having decided nothing
        is pending, naming thousands of files for snakemake to stat is exactly the
        cost being avoided."""
        if self.skip_scan:
            return []
        items = self.items() if items is None else items
        return [p for item in items for p in products(item) if p is not None]

    # ---- recording a clean scan ----

    @property
    def found_work(self):
        return self._found_work

    def record_if_clean(self, log=None):
        """Write the stamp when a FULL scan found every product present, so the next
        run can skip the scan.  Call last in the Snakefile: only there has every
        stage's pending() run, so only there is found_work final.  A scan that found
        work never records itself as clean; deleting the stamp costs one slow run."""
        if self.skip_scan or self._found_work:
            return False
        fileOps.ensureFileDir(self.stamp)
        with open(self.stamp, "w") as fh:
            fh.write(self.fingerprint)
        if log is not None:
            log(f"per-item scan: nothing missing, recorded {self.stamp}")
        return True
