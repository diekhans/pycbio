"""
Rules to run cluster jobs with UCSC parasol system.

A cluster batch is run in three phases
   1) setup - define jobs and create temporary files required by the batch
   2) run - run the batch on the cluster
   3) finish - combine results of cluster jobs and remove temporary files.

Each batch has a unique name which is used for tracking the
state of the batch

"""
