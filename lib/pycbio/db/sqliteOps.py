# Copyright 2006-2022 Mark Diekhans
"""
Functions and classes for working with Sqlite 3 databases.
"""
import apsw

from pycbio.sys.objDict import ObjDict

# FIXME: no tests
# FIXME: need logging of sql
# FIXME: add options to do logging, both of exceptions (apsw handler) and queries
# FIXME  gets Obj of rows:

class SqliteOpsError(Exception):
    "Error wrapped around sqlite exceptions to add information"
    pass

class QueryOpts:
    """Special options to control query. Use maxErrorLenSql and maxErrorLenArgs
    to limit size of formatting of SQL and arguments in error messages.."""
    def __init__(self, *, maxErrorLenSql=None, maxErrorLenArgs=200):
        self.maxErrorLenSql = maxErrorLenSql
        self.maxErrorLenArgs = maxErrorLenArgs


DEFAULT_QUERY_OPTS = QueryOpts()

def objDictRowFactory(cur, row):
    """Row factory to return a ObjDict of the result.  Note that non-unique
    names from multiple tables will end up with the last column of the same
    name winning.  In sane cases, these will have the same value"""
    return ObjDict(zip((t[0] for t in cur.description), row))

def _trimMsgAsNeeded(qopts, msg):
    if (qopts.maxErrorLenSql is not None) and (len(msg) > qopts.maxErrorLenSql):
        msg = msg[0:qopts.maxErrorLenSql] + '...'
    return msg

def _createSqlExcept(sql, args, qopts):
    """create exception with SQL and optionally args, possibly truncating sql
    query and args to limit size"""
    if qopts.maxErrorLenSql is not None:
        if len(sql) > qopts.maxErrorLenSql:
            sql = sql[0:qopts.maxErrorLenSql] + '...'
    msg = "failed query: '{}'".format(_trimMsgAsNeeded(qopts, sql))

    if args is not None:
        msg += ' with args {}'.format(_trimMsgAsNeeded(qopts, str(args)))

    return SqliteOpsError(msg)

def connect(sqliteDb, create=False, readonly=True, timeout=None, synchronous=None, rowFactory=None):
    """Connect to an sqlite3 database.  If create is specified, then database
    is created if it doesn't exist.  If sqliteDb is None, and in-memory data
    is created with create and readonly flags being ignored. If create is True,
    readonly is set to False.  Set rowFactory=objDictRowFactory to get objects for rows."""
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
    if rowFactory is not None:
        conn.setrowtrace(rowFactory)
    return conn

def setSynchronous(conn, mode):
    if mode is False:
        mode = "OFF"
    elif mode is True:
        mode = "NORMAL"
    execute(conn, "PRAGMA synchronous={}".format(mode))

class SqliteCursor:
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

def quote(val):
    "generate a value that is safe to use directly in a SELECT"
    return apsw.format_sql_value(val)

def makeInSeqArg(vals):
    """generate the IN operator sequence, including parentheses for a set of
    values.  Use this for 'SELECT ... WHERE foo in ?'."""
    return "({})".format(','.join(apsw.format_sql_value(v) for v in vals))


def execute(conn, sql, args=None, *, qopts=DEFAULT_QUERY_OPTS):
    """Run an SQL query on a connection that does not return rows.
    Args are formatted in sql using APWS format (? or :named).

    Use maxErrorLenSql and maxErrorLenArgs to limit size of formatting of SQL
    and arguments in error messages. Set to None to not limit.
    """
    with SqliteCursor(conn) as cur:
        try:
            cur.execute(sql, args)
        except apsw.Error as ex:
            raise _createSqlExcept(sql, args, qopts) from ex


def executeMany(conn, sql, args=None, *, qopts=DEFAULT_QUERY_OPTS):
    """Run multiple SQL queries on a connection that does not return rows.
    Args are formatted in sql using APWS format (? or :named).


    Use maxErrorLenSql and maxErrorLenArgs to limit size of formatting of SQL
    and arguments in error messages. Set to None to not limit.
    """
    with SqliteCursor(conn) as cur:
        try:
            cur.executemany(sql, args)
        except apsw.Error as ex:
            raise _createSqlExcept(sql, args, qopts) from ex


def query(conn, sql, args=None, *, rowFactory=None, qopts=DEFAULT_QUERY_OPTS):
    """Generator to run an SQL query on a connection"
    Args are formatted in sql using APWS format (? or :named).


    Use maxErrorLenSql and maxErrorLenArgs to limit size of formatting of SQL
    and arguments in error messages. Set to None to not limit.
    """
    with SqliteCursor(conn, rowFactory=rowFactory) as cur:
        try:
            cur.execute(sql, args)
            for row in cur:
                yield row
        except apsw.Error as ex:
            raise _createSqlExcept(sql, args, qopts) from ex

def haveTable(conn, table):
    "check if a table exists"
    sql = """SELECT count(*) FROM sqlite_master WHERE (type = "table") AND (name = ?);"""
    with SqliteCursor(conn) as cur:
        cur.execute(sql, (table, ))
        row = next(cur)
        return row[0] > 0


fastLoadPragmas = (
    f"PRAGMA cache_size = {64 * 1048576};"
    "PRAGMA synchronous = OFF;"
    "PRAGMA journal_mode = OFF;"
    "PRAGMA locking_mode = EXCLUSIVE;"
    "PRAGMA count_changes = OFF;"
    "PRAGMA temp_store = MEMORY;"
    "PRAGMA auto_vacuum = NONE;"
    "PRAGMA cache_spill = OFF;"
    f"PRAGMA mmap_size = {256 * 1048576};"
    f"PRAGMA page_size = {16 * 1024};"
)


def setFastLoadPragmas(conn):
    """setup pragmas for faster bulk loading"""
    # can't have a transaction open
    cur = conn.cursor()
    try:
        cur.execute(fastLoadPragmas).fetchall()
    finally:
        cur.close()

def optimize(conn, *, vacuum=False):
    """run database optimizations"""
    if vacuum:
        conn.execute("VACUUM;")
    conn.execute("ANALYZE;")
    conn.execute("PRAGMA optimize;")

def loadExtension(conn, lib):
    "load a sqlite3 extension"
    conn.enableloadextension(True)
    conn.loadextension(lib)
