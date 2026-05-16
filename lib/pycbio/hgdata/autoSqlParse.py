# Copyright 2006-2025 Mark Diekhans
"""Parser for UCSC autoSql (.as) schema files.

Returns an in-memory AST suitable for code generators.  Only the subset of the
autoSql language commonly used in hg/lib/*.as is supported (`table` declarations
with scalar, fixed/variable array, enum and set fields).  Nested `simple`/`object`
fields are not implemented.

The grammar is documented in kent/src/hg/autoSql/autoSql.doc.
"""

import re
from dataclasses import dataclass


_BASIC_TYPES = frozenset((
    "int", "uint", "short", "ushort", "byte", "ubyte", "bigint",
    "float", "char", "string", "lstring",
))
_DECL_TYPES = frozenset(("table", "object", "simple"))
_INDEX_TYPES = frozenset(("primary", "index", "unique"))


class AutoSqlParseError(Exception):
    """Error parsing an autoSql (.as) file."""


@dataclass(frozen=True)
class AsType:
    """An autoSql field type.

    name: one of the basic types (int, uint, ..., string, lstring, char) or
          'enum' / 'set'.
    isArray: True for `type[N]` or `type[fieldName]` declarations.
    arraySize: int (fixed-size array) or str (variable-length array, the name of
               the count field declared earlier) or None for non-array types.
    enumValues: tuple[str] of symbols for enum/set types; None otherwise.
    """
    name: str
    isArray: bool = False
    arraySize: object = None
    enumValues: tuple = None


@dataclass(frozen=True)
class AsField:
    name: str
    type: AsType
    comment: str
    indexType: str = None    # 'primary' | 'index' | 'unique' | None
    indexSize: int = None    # prefix-index width if specified
    auto: bool = False


@dataclass(frozen=True)
class AsObject:
    """A table/object/simple declaration."""
    declType: str            # 'table' | 'object' | 'simple'
    name: str
    comment: str
    fields: tuple            # tuple[AsField, ...]
    indexType: str = None
    indexSize: int = None
    auto: bool = False


_TOKEN_RE = re.compile(r"""
    (?P<ws>\s+) |
    (?P<hashcomment>\#[^\n]*) |
    (?P<linecomment>//[^\n]*) |
    "(?P<string>[^"]*)" |
    (?P<ident>[A-Za-z_][A-Za-z_0-9]*) |
    (?P<number>\d+) |
    (?P<punct>[(){};,\[\]])
""", re.VERBOSE)


def _tokenize(text, fileName):
    pos = 0
    line = 1
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if m is None:
            raise AutoSqlParseError(
                f"{fileName}:{line}: unexpected character {text[pos]!r}")
        kind = m.lastgroup
        value = m.group(kind)
        pos = m.end()
        if kind in ("ws", "hashcomment", "linecomment"):
            line += value.count("\n")
            continue
        yield (kind, value, line)
        line += value.count("\n")


class _TokenStream:
    def __init__(self, tokens, fileName):
        self._tokens = list(tokens)
        self._pos = 0
        self.fileName = fileName

    def peek(self):
        if self._pos >= len(self._tokens):
            return (None, None, -1)
        return self._tokens[self._pos]

    def next(self):
        tok = self.peek()
        if tok[0] is not None:
            self._pos += 1
        return tok

    def eof(self):
        return self._pos >= len(self._tokens)

    def expect(self, kind, value=None):
        tok = self.next()
        if tok[0] != kind or (value is not None and tok[1] != value):
            want = value if value is not None else kind
            raise AutoSqlParseError(
                f"{self.fileName}:{tok[2]}: expected {want!r}, got {tok[1]!r}")
        return tok


def _parseIndexClause(ts):
    """Parse optional `(primary|index|unique)[width]? auto?` suffix.
    Returns (indexType, indexSize, auto)."""
    indexType = None
    indexSize = None
    auto = False
    kind, value, _ = ts.peek()
    if kind == "ident" and value in _INDEX_TYPES:
        ts.next()
        indexType = value
        kind, value, _ = ts.peek()
        if kind == "punct" and value == "[":
            ts.next()
            tok = ts.expect("number")
            indexSize = int(tok[1])
            ts.expect("punct", "]")
    kind, value, _ = ts.peek()
    if kind == "ident" and value == "auto":
        ts.next()
        auto = True
    return indexType, indexSize, auto


def _parseFieldType(ts):
    """Parse a field type spec.  Returns AsType."""
    kind, value, lineNo = ts.next()
    if kind != "ident":
        raise AutoSqlParseError(
            f"{ts.fileName}:{lineNo}: expected type name, got {value!r}")
    if value in ("enum", "set"):
        ts.expect("punct", "(")
        values = []
        while True:
            tok = ts.expect("ident")
            values.append(tok[1])
            kind2, value2, _ = ts.peek()
            if kind2 == "punct" and value2 == ",":
                ts.next()
                continue
            break
        ts.expect("punct", ")")
        return AsType(name=value, enumValues=tuple(values))
    if value not in _BASIC_TYPES:
        raise AutoSqlParseError(
            f"{ts.fileName}:{lineNo}: unsupported field type {value!r} "
            f"(nested simple/object/table fields not implemented)")
    typeName = value
    kind2, value2, _ = ts.peek()
    if kind2 == "punct" and value2 == "[":
        ts.next()
        tok = ts.next()
        if tok[0] == "number":
            arraySize = int(tok[1])
        elif tok[0] == "ident":
            arraySize = tok[1]
        else:
            raise AutoSqlParseError(
                f"{ts.fileName}:{tok[2]}: expected number or field name "
                f"in array, got {tok[1]!r}")
        ts.expect("punct", "]")
        return AsType(name=typeName, isArray=True, arraySize=arraySize)
    return AsType(name=typeName)


def _parseField(ts):
    typeSpec = _parseFieldType(ts)
    nameTok = ts.expect("ident")
    fieldName = nameTok[1]
    indexType, indexSize, auto = _parseIndexClause(ts)
    ts.expect("punct", ";")
    commentTok = ts.expect("string")
    return AsField(name=fieldName, type=typeSpec, comment=commentTok[1],
                   indexType=indexType, indexSize=indexSize, auto=auto)


def _parseDeclaration(ts):
    kindTok = ts.next()
    if kindTok[0] != "ident" or kindTok[1] not in _DECL_TYPES:
        raise AutoSqlParseError(
            f"{ts.fileName}:{kindTok[2]}: expected 'table'/'object'/'simple', "
            f"got {kindTok[1]!r}")
    declType = kindTok[1]
    nameTok = ts.expect("ident")
    indexType, indexSize, auto = _parseIndexClause(ts)
    commentTok = ts.expect("string")
    ts.expect("punct", "(")
    fields = []
    while True:
        kind, value, _ = ts.peek()
        if kind == "punct" and value == ")":
            ts.next()
            break
        fields.append(_parseField(ts))
    return AsObject(declType=declType, name=nameTok[1], comment=commentTok[1],
                    fields=tuple(fields), indexType=indexType,
                    indexSize=indexSize, auto=auto)


def parseAutoSqlText(text, fileName="<string>"):
    """Parse autoSql source text. Returns tuple[AsObject, ...]."""
    ts = _TokenStream(_tokenize(text, fileName), fileName)
    objects = []
    while not ts.eof():
        objects.append(_parseDeclaration(ts))
    return tuple(objects)


def parseAutoSql(path):
    """Parse an autoSql (.as) file. Returns tuple[AsObject, ...]."""
    with open(path) as fh:
        text = fh.read()
    return parseAutoSqlText(text, fileName=path)
