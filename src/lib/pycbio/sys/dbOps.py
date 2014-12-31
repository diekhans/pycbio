# Copyright 2006-2012 Mark Diekhans
"""Operations on dbapi objects"""
import MySQLdb, warnings


_mySqlErrorOnWarnDone = False

def mySqlSetErrorOnWarn():
    """Turn most warnings into errors except for those that are Notes from
    `drop .. if exists'.  This only adds warnings the firs time its called"""
    # the drop warnings could also be disabled with a set command.
    global _mySqlErrorOnWarnDone
    if not _mySqlErrorOnWarnDone:
        warnings.filterwarnings('error', category=MySQLdb.Warning)
        warnings.filterwarnings("ignore", "Unknown table '.*'")
        warnings.filterwarnings("ignore", "Can't drop database '.*'; database doesn't exist")
        _mySqlErrorOnWarnDone = True


def cursorColIdxMap(cur):
    """generate a hash of column name to row index given a cursor that has had
    a select executed"""
    m = {}
    for i in xrange(len(cur.description)):
        m[cur.description[i][0]] = i
    return m

def queryConnection(conn, sql):
    "generator to run an SQL query on a connection"
    cur = conn.cursor()
    try:
        cur.execute(sql)
        for row in cur:
            yield row
    finally:
        cur.close()

def haveTableLike(conn, pattern, db=None):
    frm = "" if db == None else " from " + db
    # FIXME: mysql-specific
    return len(list(queryConnection(conn, 'show tables' + frm + ' like "' + pattern + '";'))) > 0

