# Copyright 2006-2017 Mark Diekhans
"""
Functions and classes for working with Sqlite 3 databases.
"""
import apsw


def sqliteConnect(sqliteDb, create=False, readonly=True, timeout=None, synchronous=None):
    """Connect to an sqlite3 database.  If create is specified, then database
    is created if it doesn't exist.  If sqliteDb is None, and in-memory data
    is created with create and readonly flags being ignored. If create is True,
    readonly is set to False."""
    if create:
        readonly = False
    if sqliteDb is None:
        sqliteDb = ":memory:"
        create = True
        readonly = False

    flags = apsw.SQLITE_OPEN_READONLY if readonly else apsw.SQLITE_OPEN_READWRITE
    if create:
        flags |= apsw.SQLITE_OPEN_CREATE
    kwargs = {"flags": flags}
    if timeout is not None:
        kwargs["timeout"] = timeout
    conn = apsw.Connection(sqliteDb, **kwargs)
    if synchronous is not None:
        sqliteSetSynchronous(conn, synchronous)
    return conn


def sqliteSetSynchronous(conn, mode):
    if mode is False:
        mode = "OFF"
    elif mode is True:
        mode = "NORMAL"
    with SqliteCursor(conn) as cur:
        cur.execute("PRAGMA synchronous={}".format(mode))


class SqliteCursor(object):
    """context manager creating an sqlite cursor in a single transaction"""
    def __init__(self, conn, rowFactory=None):
        self.conn = conn
        self.rowFactory = rowFactory
        self.trans = None
        self.cur = None

    def __enter__(self):
        self.trans = self.conn.__enter__()
        self.cur = self.conn.cursor()
        if self.rowFactory is not None:
            self.cur.setrowtrace(self.rowFactory)
        return self.cur

    def __exit__(self, *args):
        self.cur.close()
        return self.trans.__exit__(*args)


def sqliteHaveTable(conn, table):
    "check if a table exists"
    sql = """SELECT count(*) FROM sqlite_master WHERE (type = "table") AND (name = ?);"""
    with SqliteCursor(conn) as cur:
        cur.execute(sql, (table, ))
        row = next(cur)
        return row[0] > 0