# Copyright 2006-2025 Mark Diekhans
"""Connect to UCSC genome database using info in .hg.conf """
from pycbio.hgdata.hgConf import HgConf
from pycbio.db import mysqlOps  # will fail is MySQLdb is not installed
import MySQLdb
import MySQLdb.cursors
import MySQLdb.converters
import copy

def connect(db="", *, confFile=None, host=None, hgConf=None,
            useAutoSqlConv=True, cursorclass=None):
    """Connect to genome mysql server, using confFile( default is ~/.hg.conf),
    or pre-parsed HgConf. If useAutoSqlConv is True, blob fields, as used to
    arrays, are converted to str rather than stored as bytes.   Use
    cusrorclass=mysqlOps.DictCursor for a dictionary cursor)
    """
    if hgConf is None:
        hgConf = HgConf.obtain(confFile)
    conv = getAutoSqlConverter() if useAutoSqlConv else None
    if host is None:
        host = hgConf["db.host"]
    return mysqlOps.connect(host=host, user=hgConf["db.user"], passwd=hgConf["db.password"], db=db,
                            cursorclass=cursorclass, conv=conv)

def _binaryDecode(v):
    return v.decode()

def getAutoSqlConverter():
    """get a MySQLdb that handles text in blobs"""
    conv = copy.copy(MySQLdb.converters.conversions)
    fts = MySQLdb.constants.FIELD_TYPE
    # these are all listed as conversion to bytes in MySQLdb.converters.conversions
    # FIXME: test could be done by looking up fields rathering listing
    for ft in (fts.VARCHAR, fts.JSON, fts.STRING, fts.VAR_STRING,
               fts.TINY_BLOB, fts.MEDIUM_BLOB, fts.LONG_BLOB, fts.BLOB):
        conv[ft] = _binaryDecode
    return conv
