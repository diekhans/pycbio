# Copyright 2006-2010 Mark Diekhans
"""Connect to UCSC genome database using info in .hg.conf """
from pycbio.hgdata import HgConf
import MySQLdb

def connect(db=None,  confFile=None):
    """connect to genome mysql server, using confFile or ~/.hg.conf"""
    conf = HgConf.obtain(confFile)
    return MySQLdb.Connect(host=conf["db.host"], user=conf["db.user"], passwd=conf["db.password"], db=db)
    
