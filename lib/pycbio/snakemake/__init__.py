"""Support for Snakemake workflows that fan a stage out over a cluster.

Nothing here knows anything about any project.  What it packages is one shape:
a workflow whose stages each run one JOB per ITEM (assembly, sample, chromosome)
over a batch system, where the items number in the hundreds and the products in
the tens of thousands.

  * ProductScan  -- per-product staleness, and the stamp that makes deciding
                    "nothing to do" cheap.
  * BatchRunner  -- a stage's jobs as one batch, so snakemake sees one rule
                    rather than thousands of jobs.
  * ParasolBatch / SlurmBatch -- the two batch systems behind one contract.
  * timed        -- per-rule elapsed/CPU/wait, to stderr and a TSV log.

fileOps.fast_remove is the companion for clean rules: it discards big trees
without waiting for the recursive delete.

Why the shape, and what it costs to get wrong -- all three were measured on the
workflow this came from (~460 assemblies, ~11k products):

  1. Let the batch system own the per-job work.  One snakemake job per unit of
     work would mean thousands of scheduler objects; instead a stage writes a job
     file, blocks on one batch, and per-job incrementality comes from the tools
     themselves skipping completed outputs.  Snakemake tracks only whether the
     stage is done, via a sentinel.
  2. Declare products, not provenance.  A stage's rule outputs are the products
     it is missing, so adding one item builds that item and touching the catalog
     builds nothing.  `rule all` must then REQUEST every leaf product: snakemake
     prunes a job whose outputs exist, and a missing INPUT of a pruned job does
     not un-prune it.
  3. Make "nothing to do" cheap.  Statting every product is O(items x products)
     -- ~11k NFS stats, ~40s, paid on every invocation including the ones with
     no work.  ProductScan's stamp reduces that to reading one file.

One more piece is configuration rather than code, and a workflow of this shape
needs it -- in profiles/<name>/config.yaml:

    drop-metadata: true
    rerun-triggers: [mtime]

Because every stage takes the upstream stage's full product list as its input,
snakemake would write one metadata record per OUTPUT file with that entire input
list embedded: ~250KB per output, 55MB for a 100-output run, and 210s of the
255s a stage took spent writing small files after the real work was done -- in
an uninterruptible filesystem wait, indistinguishable from a hang.  Dropping it
then forces the second line: with no input-set record to refresh, the "input set
changed" rerun trigger fires forever, dragging finished stages into every run.
Nothing here needs either, since staleness is decided by missing products.  What
it costs: --summary, --list-changes, and the code/params/input-set triggers.
"""
# Copyright 2006-2026 Mark Diekhans

from pycbio.snakemake.timing import (set_timing_log, get_timing_log, timed,  # noqa: F401
                                     report_timing, append_timing_log)
from pycbio.snakemake.productScan import (ProductScan, outputs_current,  # noqa: F401
                                          env_flag)
from pycbio.snakemake.batch import (BatchRunner, ParasolBatch, SlurmBatch)  # noqa: F401
