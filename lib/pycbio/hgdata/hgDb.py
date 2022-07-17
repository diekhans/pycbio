# Copyright 2006-2012 Mark Diekhans
"""Connect to UCSC genome database using info in .hg.conf """
from pycbio.hgdata.hgConf import HgConf
from pycbio.db import mysqlOps
import MySQLdb
import MySQLdb.cursors
import MySQLdb.converters
import copy

def connect(db="", *, confFile=None, host=None, hgConf=None,
            useAutoSqlConv=True, cursorclass=MySQLdb.cursors.DictCursor):
    """Connect to genome mysql server, using confFile( default is ~/.hg.conf),
    or pre-parsed HgConf. If useAutoSqlConv is True, blob fields, as used to
    arrays, are converted to str rather than stored as bytes.   Defaults to DictCursor"""
    if hgConf is None:
        hgConf = HgConf.obtain(confFile)
    conv = getAutoSqlConverter() if useAutoSqlConv else None
    if host is None:
        host = hgConf["db.host"]
    return mysqlOps.connect(host=host, user=hgConf["db.user"], passwd=hgConf["db.password"], db=db,
                            cursorclass=cursorclass, conv=conv)


def getAutoSqlConverter():
    """get a MySQLdb that handles text in blobs"""
    conv = copy.copy(MySQLdb.converters.conversions)
    fts = MySQLdb.constants.FIELD_TYPE
    for ft in (fts.TINY_BLOB, fts.MEDIUM_BLOB, fts.LONG_BLOB, fts.BLOB):
        conv[ft] = [(MySQLdb.constants.FLAG.BINARY, lambda v: v.decode())]
    return conv
