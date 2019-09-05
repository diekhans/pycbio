# Copyright 2006-2017 Mark Diekhans
"""
Functions and classes for working with Sqlite 3 databases.
"""
import apsw


def connect(sqliteDb, create=False, readonly=True, timeout=None, synchronous=None):
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
    try:
        conn = apsw.Connection(sqliteDb, **kwargs)
    except apsw.CantOpenError as ex:
        raise apsw.CantOpenError(str(apsw.CantOpenError) + ": " + sqliteDb) from ex
    if synchronous is not None:
        setSynchronous(conn, synchronous)
    return conn


def setSynchronous(conn, mode):
    if mode is False:
        mode = "OFF"
    elif mode is True:
        mode = "NORMAL"
    with SqliteCursor(conn) as cur:
        cur.execute("PRAGMA synchronous={}".format(mode))


class SqliteCursor(object):
    """Context manager creating an sqlite cursor and a transaction.
    """
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


def query(conn, sql, args=None):
    "generator to run an SQL query on a connection"
    with SqliteCursor(conn) as cur:
        cur.execute(sql, args)
        for row in cur:
            yield row


def haveTable(conn, table):
    "check if a table exists"
    sql = """SELECT count(*) FROM sqlite_master WHERE (type = "table") AND (name = ?);"""
    with SqliteCursor(conn) as cur:
        cur.execute(sql, (table, ))
        row = next(cur)
        return row[0] > 0


fastLoadPragmas = (
    "PRAGMA cache_size = 1000000;"
    "PRAGMA synchronous = OFF;"
    "PRAGMA journal_mode = OFF;"
    "PRAGMA locking_mode = EXCLUSIVE;"
    "PRAGMA count_changes = OFF;"
    "PRAGMA temp_store = MEMORY;"
    "PRAGMA auto_vacuum = NONE;")


def setFastLoadPragmas(conn):
    """setup pragmas for faster bulk loading"""
    with SqliteCursor(conn) as cur:
        cur.execute(fastLoadPragmas)
