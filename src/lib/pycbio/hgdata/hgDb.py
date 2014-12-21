# Copyright 2006-2012 Mark Diekhans
"""Connect to UCSC genome database using info in .hg.conf """
from pycbio.hgdata.hgConf import HgConf
from pycbio.sys import dbOps
import MySQLdb
import MySQLdb.cursors

dbOps.mySqlSetErrorOnWarn()

def connect(db="",  confFile=None, dictCursor=False, host=None):
    """connect to genome mysql server, using confFile or ~/.hg.conf"""
    conf = HgConf.obtain(confFile)
    cursorclass = MySQLdb.cursors.DictCursor if dictCursor else MySQLdb.cursors.Cursor
    if host == None:
        host = conf["db.host"]
    return MySQLdb.Connect(host=host, user=conf["db.user"], passwd=conf["db.password"], db=db, cursorclass=cursorclass)
    
