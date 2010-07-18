"""
Rules to run cluster jobs with UCSC parasol system.

A cluster batch is run in three phases
   1) setup - define jobs and create temporary files required by the batch
   2) run - run the batch on the cluster
   3) finishup - combine results of cluster jobs and remove temporary files.

Each batch has a unique name which is used for tracking the state of the
batch.  The state is tracked via flag files, indicating

"""
from pycbio.exrun.Graph import Rule

class Parasol(Rule):
    """Construct a parasol batch rule.  A specific rule extends this class
    implementing the setup and finishup methods.  The name must be unique for
    a given exprName.  It is used to track the state of partially completed
    batches.
    """
    def __init__(self, name, requires=None, produces=None, shortName=None):
        Rule.__init__(self, name, requires=requires, produces=produces, shortName=shortName)



    
