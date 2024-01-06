# Copyright 2006-2022 Mark Diekhans
"""Operations for accessing mysql"""
import warnings
from pycbio import PycbioException
try:
    import MySQLdb   # mysqlclient is required for python 3
    from MySQLdb.cursors import DictCursor  # noqa: F401
    from MySQLdb.cursors import Cursor
    import MySQLdb.converters
except ModuleNotFoundError as ex:
    raise PycbioException("MySQL/MariaDb support not available without mysqlclient (MySQLdb) package") from ex

_mySqlErrorOnWarnDone = False

def mySqlSetErrorOnWarn():
    """Turn most warnings into errors except for those that are Notes from
    `drop .. if exists'.  This only adds warnings the firs time its called"""
    # the drop warnings could also be disabled with a set command.
    global _mySqlErrorOnWarnDone
    if not _mySqlErrorOnWarnDone:
        warnings.filterwarnings('error', category=MySQLdb.Warning)
        warnings.filterwarnings("ignore", message="Unknown table '.*'")
        warnings.filterwarnings("ignore", message="Can't drop database '.*'; database doesn't exist")
        warnings.filterwarnings("ignore", message="PY_SSIZE_T_CLEAN will be required for '#' formats")
        _mySqlErrorOnWarnDone = True


def connect(*, host=None, port=None, user=None, passwd=None, db=None, cursorclass=None,
            conv=None):
    """Connect to genome mysql server, using explict parameters.
    Use cursorclass=mysqlOps.DictCursor to get dictionary results
    """
    if not _mySqlErrorOnWarnDone:
        mySqlSetErrorOnWarn()
    kwargs = {}
    loc = locals()
    for arg in ("host", "port", "user", "passwd", "db", "cursorclass", "conv"):
        if loc[arg] is not None:
            kwargs[arg] = loc[arg]
    return MySQLdb.Connect(**kwargs)


def execute(conn, sql, args=None):
    "execute SQL query on a connection that returns no result"
    cur = conn.cursor()
    try:
        cur.execute(sql, args)
    finally:
        cur.close()


def query(conn, sql, args=None, *, cursorclass=None):
    "generator to run an SQL query on a connection"
    cur = conn.cursor(cursorclass=cursorclass)
    try:
        cur.execute(sql, args)
        for row in cur:
            yield row
    finally:
        cur.close()


def getTablesLike(conn, pattern, db=None):
    frm = "" if db is None else "from " + db
    sql = "show tables {} like \"{}\"".format(frm, pattern)
    cur = conn.cursor(cursorclass=Cursor)
    try:
        cur.execute(sql)
        return [row[0] for row in cur]
    finally:
        cur.close()


def haveTablesLike(conn, pattern, db=None):
    return len(getTablesLike(conn, pattern, db)) > 0
