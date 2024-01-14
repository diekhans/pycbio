# Copyright 2006-2024 Mark Diekhans
"""
Functions to check for a for being on a system with UCSC browser database
for testing.
"""
import pytest
from socket import gethostname
from pycbio.hgdata.hgConf import HgConf

browserMysqlTestHost = "hgwdev"

# check for MySQLdb
_mysqlSupportMissingMsg = None
try:
    # mysqlclient is required for python 3
    import MySQLdb  # noqa: F401
except ModuleNotFoundError:
    _mysqlSupportMissingMsg = "MySQL/MariaDb support not available without mysqlclient (MySQLdb) package"

# check for test host
_mysqlNotTestHostMsg = None
if gethostname() != browserMysqlTestHost:
    _mysqlNotTestHostMsg = f"not on a test host with a UCSC Browser database: {browserMysqlTestHost}"

# check for ~/.hg.conf
_mysqlNoHgConfMsg = None
try:
    HgConf()
except FileNotFoundError:
    _mysqlNoHgConfMsg = "hg.conf not found, database tests disabled: " + HgConf.getHgConf()

def mysqlTestsEnvAvailable():
    "can we import/run mysql tests"
    return (_mysqlSupportMissingMsg is None) and (_mysqlNotTestHostMsg is None) and (_mysqlNoHgConfMsg is None)

def skip_if_no_mysql():
    "decorator to check for not able to run mysql tests"
    def decorator(func):
        def wrapper(*args, **kwargs):
            if _mysqlSupportMissingMsg is not None:
                pytest.skip(_mysqlSupportMissingMsg)
            elif _mysqlNotTestHostMsg is not None:
                pytest.skip(_mysqlNotTestHostMsg)
            elif _mysqlNoHgConfMsg is not None:
                pytest.skip(_mysqlNoHgConfMsg)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator
