# Copyright 2006-2026 Mark Diekhans
"""Create a frameset that is a directory of locations in the genome browser.

Two directory styles are provided:

- BrowserDirStatic: server-side, paginated set of HTML pages (dir1.html,
  dir2.html, ...).  This is the original behavior.
- BrowserDirDynamic: a single HTML page that uses the Tabulator JavaScript
  library (loaded from a CDN) to provide interactive sorting, searching, and
  per-column filtering.

BrowserDir is a deprecated alias for BrowserDirStatic.
"""
import os
import re
import copy
import json
import html
import warnings
from urllib.parse import quote
from pycbio.html.htmlPage import HtmlPage
from pycbio.sys import fileOps

# FIXME: need to have ability set attributes on cells for the static output;
#        the Cell object now addresses this for the dynamic output.

defaultStyle = """
TABLE, TR, TH, TD {
    white-space: nowrap;
    border: solid;
    border-width: 1px;
    border-collapse: collapse;
}
.tableFixHead {
    overflow-y: auto;
}
.tableFixHead THEAD TH {
    position: sticky;
    top: 0;
    z-index: 1;
}
TH {
    background: #eee;
}
"""

GENOME_UCSC_URL = "https://genome.ucsc.edu"

# default Tabulator CDN version and derived asset URLs
TABULATOR_VERSION = "6.5.2"

def _tabulatorCssUrl(version):
    return f"https://unpkg.com/tabulator-tables@{version}/dist/css/tabulator.min.css"

def _tabulatorJsUrl(version):
    return f"https://unpkg.com/tabulator-tables@{version}/dist/js/tabulator.min.js"


_tagRe = re.compile(r"<[^>]+>")

def _stripTags(text):
    "remove HTML tags and unescape entities, for search/filter/sort text"
    return html.unescape(_tagRe.sub("", text))

class Cell:
    """A table cell.

    - value: plain-text content, used for searching and filtering, and as the
      default sort key.  In the static output, a bare string is treated as
      pre-encoded HTML (as before); use a Cell to attach a distinct value.
    - html: rich display content (e.g. an anchor); if None, the escaped value
      is displayed.
    - sortKey: overrides the sort value (e.g. a number or a zero-padded
      coordinate for correct genomic ordering); defaults to value.
    - cssClass: optional CSS class for the cell (used by the dynamic output).
    """
    __slots__ = ("value", "html", "sortKey", "cssClass")

    def __init__(self, value="", *, html=None, sortKey=None, cssClass=None):
        self.value = value
        self.html = html
        self.sortKey = sortKey
        self.cssClass = cssClass

def _cellHtml(cell):
    "display HTML for a cell; a bare string is pre-encoded HTML"
    if not isinstance(cell, Cell):
        return str(cell)
    if cell.html is not None:
        return cell.html
    return html.escape(str(cell.value))

def _cellText(cell):
    "plain text for a cell, used in searching and filtering"
    if not isinstance(cell, Cell):
        return _stripTags(str(cell))
    return str(cell.value)

def _cellSortKey(cell):
    "sort key for a cell"
    if isinstance(cell, Cell) and (cell.sortKey is not None):
        return cell.sortKey
    return _cellText(cell)

def _cellCssClass(cell):
    return cell.cssClass if isinstance(cell, Cell) else None

def _toNumber(v):
    "coerce a value to a number, or None if not numeric"
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _cellNumber(cell):
    "numeric value of a cell for range filtering, or None"
    if isinstance(cell, Cell):
        num = _toNumber(cell.sortKey)
        return num if num is not None else _toNumber(cell.value)
    return _toNumber(_stripTags(str(cell)))

class Row:
    "Row in the table"
    __slots__ = ("row", "key", "cssRowClass", "cssCellClasses")

    def __init__(self, row, key=None, cssRowClass=None, cssCellClasses=None):
        """Row in the table; key can be some value(s) used in Python-side
        sorting.  Each cell is either a pre-encoded HTML string or a Cell
        object.  If cssCellClasses is not None, it should be a parallel vector
        with None or the class name for the corresponding cells."""
        self.row = tuple(row)
        self.key = key
        self.cssRowClass = copy.copy(cssRowClass)
        self.cssCellClasses = copy.copy(cssCellClasses)
        assert (self.cssCellClasses is None) or (len(self.cssCellClasses) == len(row))

    def numColumns(self):
        "compute number of columns that will be generated"
        return len(self.row)

    def _mkRowStart(self):
        return "<tr>" if self.cssRowClass is None else '<tr class="{}">'.format(self.cssRowClass)

    def _cellCssClass(self, i):
        if self.cssCellClasses is not None:
            return self.cssCellClasses[i]
        return _cellCssClass(self.row[i])

    def _toHtmlCell(self, i):
        cssClass = self._cellCssClass(i)
        if cssClass is not None:
            return '<td class="{}">{}'.format(cssClass, _cellHtml(self.row[i]))
        return "<td>{}".format(_cellHtml(self.row[i]))

    def toHtmlRow(self):
        hrow = [self._mkRowStart()]
        for i in range(len(self.row)):
            hrow.append(self._toHtmlCell(i))
        hrow.append("</tr>\n")
        return "".join(hrow)

def _makeUrlArg(name, val):
    return f'{name}=' + quote(val)

def _buildTrackArgsList(trackArgs):
    # track args is dict
    if trackArgs is None:
        return []
    return [_makeUrlArg(n, v) for n, v in trackArgs.items()]

def _buildRefsList(argName, urls):
    if urls is None:
        return []
    if isinstance(urls, str):
        urls = [urls]
    return [_makeUrlArg(argName, u) for u in urls]

class BrowserDirBase:
    """Base class for genome browser directories.  Holds the common
    configuration, URL construction, and row collection.  Subclasses implement
    the directory page(s) in write().
    """

    def __init__(self, browserUrl, defaultDb, *, colNames=None, pageSize=50,
                 title=None, dirPercent=15, below=False, pageDesc=None,
                 tracks={}, initTracks={}, style=defaultStyle,
                 customTrackUrls=None, hubUrls=None):
        """The tracks arg is a dict of track name to setting, it is added to
        each URL and the initial setting of the frame. The initTracks arg is
        similar, however its only set in the initial frame and not added to
        each URL. customTrackUrls and hubUrls can be a string URL or list of URLs.
        """
        self.browserUrl = browserUrl
        if self.browserUrl.endswith("/"):
            self.browserUrl = self.browserUrl[0:-1]  # drop trailing `/', so we don't end up with '//'
        self.defaultDb = defaultDb
        self.colNames = colNames
        self.pageSize = pageSize
        self.title = title
        self.dirPercent = dirPercent
        self.below = below
        self.pageDesc = pageDesc
        self.rows = []
        self.style = style
        self.trackArgs = _buildTrackArgsList(tracks)
        self.initTrackArgs = _buildTrackArgsList(initTracks)
        self.customTrackArgs = _buildRefsList("hgt.customText", customTrackUrls)
        self.hubArgs = _buildRefsList("hubUrl", hubUrls)

    def mkUrl(self, coords, db=None, extraArgs=None):
        """can make URL to default db or another other db.  trackArgs are added if
        for defaultDb. extraArgs should list of CGI args with values quoted,
        """
        if db is None:
            db = self.defaultDb
        urlArgs = [_makeUrlArg("db", db),
                   _makeUrlArg("genome", db),
                   _makeUrlArg("position", str(coords))]
        if db == self.defaultDb:
            urlArgs.extend(self.trackArgs)
        if extraArgs is not None:
            urlArgs.extend(extraArgs)
        return self.browserUrl + "/cgi-bin/hgTracks?" + '&'.join(urlArgs)

    def mkDefaultUrl(self):
        return self.mkUrl("default", db=self.defaultDb,
                          extraArgs=self.initTrackArgs + self.customTrackArgs + self.hubArgs)

    def mkAnchor(self, coords, text=None, db=None, target="browser"):
        if text is None:
            text = str(coords)
        return "<a href=\"{}\" target={}>{}</a>".format(self.mkUrl(coords, db=db), target, text)

    def addRow(self, row, key=None, cssRowClass=None, cssCellClasses=None):
        """add a row, row can be a list of cells (HTML strings or Cell objects)
        or a Row object"""
        if not isinstance(row, Row):
            row = Row(row, key, cssRowClass, cssCellClasses)
        self.rows.append(row)

    def add(self, coords, name=None):
        """add a simple row, linking to location. If name is None, the coords are used"""
        if name is None:
            name = str(coords)
        row = [self.mkAnchor(coords, name)]
        self.addRow(row, key=coords)

    def sort(self, keyFunc=None, reverse=False):
        "sort by the keyfunc"
        if keyFunc is None:
            def keyFunc(r):
                return r.key
        self.rows.sort(key=keyFunc, reverse=reverse)

    def _mkFrame(self, dirSrc, title=None, dirPercent=15, below=False):
        """create frameset as a HtmlPage object; dirSrc is the src for the
        directory frame"""
        if below:
            fsAttr = "rows={}%%,{}%%".format(100 - dirPercent, dirPercent)
        else:
            fsAttr = "cols={}%%,{}%%".format(dirPercent, 100 - dirPercent)
        pg = HtmlPage(title=title, framesetAttrs=(fsAttr,))

        fdir = '<frame name="dir" src="{}">'.format(dirSrc)
        fbr = '<frame name="browser" src="{}">'.format(self.mkDefaultUrl())
        if below:
            pg.add(fbr)
            pg.add(fdir)
        else:
            pg.add(fdir)
            pg.add(fbr)
        return pg

    def write(self, outDir):
        raise NotImplementedError("write() must be implemented by a subclass")

class BrowserDirStatic(BrowserDirBase):
    """Create a frameset and a paginated collection of static HTML pages that
    index one or more genome browsers.
    """

    def _getPageLinks(self, pageNum, numPages, inclPageLinks):
        html = []
        # prev link
        if pageNum > 1:
            html.append("<a href=\"dir{}.html\">prev</a>".format(pageNum - 1))
        else:
            html.append("prev")

        # page number links
        if inclPageLinks:
            for p in range(1, numPages + 1):
                if p != pageNum:
                    html.append("<a href=\"dir{}.html\">{}</a>".format(p, p))
                else:
                    html.append("[{}]".format(p))

        # next link
        if pageNum < numPages:
            html.append("<a href=\"dir{}.html\">next</a>".format(pageNum + 1))
        else:
            html.append("next")
        return ", ".join(html)

    def _addPageRows(self, pg, pgRows):
        """add one set of rows to the page."""
        pg.tableStart(hclass="tableFixHead")
        if self.colNames is not None:
            pg.tableHeader(self.colNames)
        pg.add("<tbody>")   # because we don't use addTableRow
        for ent in pgRows:
            pg.add(ent.toHtmlRow())
        pg.add("</tbody>")
        pg.tableEnd()

    def _writeDirPage(self, outDir, pgRows, pageNum, numPages):
        title = "page {}".format(pageNum)
        if self.title:
            title += ": {}".format(self.title)
        pg = HtmlPage(title=title, inStyle=self.style)
        pg.h3(title)
        if self.pageDesc is not None:
            pg.add(self.pageDesc)
            pg.add("<br><br>")
        pg.add(self._getPageLinks(pageNum, numPages, False))
        self._addPageRows(pg, pgRows)
        pg.add(self._getPageLinks(pageNum, numPages, True))

        dirFile = os.path.join(outDir, "dir{}.html".format(pageNum))
        pg.writeFile(dirFile)

    def _writeDirPages(self, outDir):
        numPages = (len(self.rows) + self.pageSize - 1) // self.pageSize
        if numPages == 0:
            numPages = 1
        for pageNum in range(1, numPages + 1):
            first = (pageNum - 1) * self.pageSize
            last = first + (self.pageSize - 1)
            pgRows = self.rows[first:last]
            self._writeDirPage(outDir, pgRows, pageNum, numPages)

    def write(self, outDir):
        fileOps.ensureDir(outDir)
        frame = self._mkFrame("dir1.html", self.title, self.dirPercent, self.below)
        frame.writeFile(os.path.join(outDir, "index.html"))
        self._writeDirPages(outDir)

class BrowserDir(BrowserDirStatic):
    """Deprecated alias for BrowserDirStatic."""

    def __init__(self, *args, **kwargs):
        warnings.warn("BrowserDir is deprecated; use BrowserDirStatic",
                      DeprecationWarning, stacklevel=2)
        super().__init__(*args, **kwargs)


# JavaScript helpers shared by all dynamic pages.  These are static (contain no
# per-page data), so they are emitted verbatim.
_dynamicScriptHelpers = """
function _keySort(a, b, aRow, bRow, column, dir, params) {
    var x = aRow.getData()[params.field];
    var y = bRow.getData()[params.field];
    if (x === y) return 0;
    return (x > y) ? 1 : -1;
}
function _colFilter(headerValue, rowValue, rowData, params) {
    var t = ("" + (rowData[params.field] || "")).toLowerCase();
    return t.indexOf(("" + headerValue).toLowerCase()) > -1;
}
function _anySearch(data, params) {
    for (var i = 0; i < params.fields.length; i++) {
        var t = ("" + (data[params.fields[i]] || "")).toLowerCase();
        if (t.indexOf(params.value) > -1) return true;
    }
    return false;
}
function _rangeEditor(cell, onRendered, success, cancel, params) {
    var wrap = document.createElement("span");
    var lo = document.createElement("input");
    var hi = document.createElement("input");
    wrap.className = "dirRange";
    lo.type = hi.type = "number";
    lo.placeholder = "min";
    hi.placeholder = "max";
    function val() {
        return {min: lo.value === "" ? null : parseFloat(lo.value),
                max: hi.value === "" ? null : parseFloat(hi.value)};
    }
    // Tabulator's live filter calls success(editorElement.value); expose the
    // range object as the element's value so that path works, not just ours.
    Object.defineProperty(wrap, "value", {get: val});
    function commit() { success(val()); }
    function stop(e) { e.stopPropagation(); }
    function key(e) { if (e.key === "Escape") cancel(); e.stopPropagation(); }
    lo.addEventListener("input", commit);
    hi.addEventListener("input", commit);
    lo.addEventListener("keydown", key);
    hi.addEventListener("keydown", key);
    lo.addEventListener("mousedown", stop);
    hi.addEventListener("mousedown", stop);
    wrap.appendChild(lo);
    wrap.appendChild(hi);
    return wrap;
}
function _rangeFilter(headerValue, rowValue, rowData, params) {
    var n = rowData[params.field];
    if (n === null || n === undefined || n === "") return false;
    n = parseFloat(n);
    if (isNaN(n)) return false;
    if (headerValue.min !== null && n < headerValue.min) return false;
    if (headerValue.max !== null && n > headerValue.max) return false;
    return true;
}
function _rangeEmpty(value) {
    return (value == null) || (value.min == null && value.max == null);
}
"""

_dynamicStyle = """
html, body { height: 100%; margin: 0; }
body { display: flex; flex-direction: column; font-family: sans-serif; }
#dirSearchBar { padding: 4px; flex: 0 0 auto; }
#dirSearch { width: 20em; }
#dirTable { flex: 1 1 auto; }
.tabulator-row.dirCurrent { background-color: #ffe08a !important;
                            box-shadow: inset 3px 0 0 #d97706; }
.tabulator-row .tabulator-cell.dirWrap { white-space: normal;
                                         overflow: visible;
                                         text-overflow: clip;
                                         word-break: break-word; }
.dirRange { display: flex; gap: 2px; }
.dirRange input { width: 50%; box-sizing: border-box; }
.dirRange input::-webkit-outer-spin-button,
.dirRange input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.dirRange input[type=number] { -moz-appearance: textfield; appearance: textfield; }
"""

class BrowserDirDynamic(BrowserDirBase):
    """Create a frameset whose directory frame is a single interactive page,
    using the Tabulator JavaScript library (loaded from a CDN) to provide
    sorting, a global search box, and per-column filtering.

    Per-column sort keys and filter text come from Cell objects; rows added as
    plain HTML strings sort and filter on their stripped text.
    """

    def __init__(self, browserUrl, defaultDb, *, globalSearch=True,
                 headerFilters=True, headerWrap=False, layout="fitColumns",
                 colDefs=None, tabulatorVersion=TABULATOR_VERSION,
                 tabulatorOptions=None, **kwargs):
        """globalSearch adds a search box that matches across all columns.
        headerFilters adds a per-column filter input under each header.
        headerWrap word-wraps the column-name titles of all columns (a column
        can override this with its own headerWrap in colDefs).  layout is the
        Tabulator layout mode; the default "fitColumns" makes the columns fill
        and resize with the window.

        colDefs is an optional dict giving per-column behavior, keyed by column
        name or zero-based index; each value is a dict with any of:
          - wrap:       True to word-wrap the cell content
          - headerWrap: True/False to word-wrap this column's name (overrides
                        the table-wide headerWrap)
          - width:      fixed width (int pixels or CSS string); the column does
                        not flex
          - minWidth:   minimum width in pixels; a flexible column will not
                        shrink (or clip) below this, so use it to keep a column
                        at its data width
          - grow:       widthGrow, the relative share of leftover width a
                        flexible column claims (default 3 for a wrap column)
          - shrink:     widthShrink
          - filter:     "text" (default, substring match), "range" (numeric
                        min/max filter), or "none" (no header filter)
          - align:      horizontal alignment "left", "center", or "right"
                        (header and cells); "range" columns default to "right"
        A wrapping column with no explicit width defaults to grow=3 and
        minWidth=120 so it absorbs width and re-flows as the window resizes.
        A "range" filter column needs a numeric value per cell (a Cell whose
        sortKey or value is a number, or a plain numeric cell).

        tabulatorOptions is an optional dict merged into the Tabulator
        configuration.
        """
        super().__init__(browserUrl, defaultDb, **kwargs)
        self.globalSearch = globalSearch
        self.headerFilters = headerFilters
        self.headerWrap = headerWrap
        self.layout = layout
        self.colDefs = colDefs or {}
        self.tabulatorVersion = tabulatorVersion
        self.tabulatorOptions = tabulatorOptions

    def _colTitles(self):
        "column titles, defaulting to positional names if colNames is None"
        if self.colNames is not None:
            return list(self.colNames)
        ncols = self.rows[0].numColumns() if self.rows else 0
        return ["col{}".format(i + 1) for i in range(ncols)]

    def _colDef(self, i, title):
        "per-column definition dict, looked up by name then index"
        cd = self.colDefs.get(title)
        if cd is None:
            cd = self.colDefs.get(i)
        return cd or {}

    def _applyColDef(self, entry, cd):
        "merge a colDefs entry into the client column spec, with wrap defaults"
        wrap = bool(cd.get("wrap"))
        if wrap:
            entry["wrap"] = True
        if "width" in cd:
            entry["width"] = cd["width"]
        flexWrap = wrap and ("width" not in cd)   # a wrap column that flexes
        grow = cd.get("grow", 3 if flexWrap else None)
        if grow is not None:
            entry["grow"] = grow
        minWidth = cd.get("minWidth", 120 if flexWrap else None)
        if minWidth is not None:
            entry["minWidth"] = minWidth
        if "shrink" in cd:
            entry["shrink"] = cd["shrink"]

    def _colFilterType(self, i, title):
        "header filter type for a column: text, range, or none"
        return self._colDef(i, title).get("filter", "text")

    def _colSpec(self):
        "specification of columns, passed to the client as JSON"
        spec = []
        for i, title in enumerate(self._colTitles()):
            entry = {"title": title, "field": "c{}".format(i),
                     "sortField": "c{}s".format(i),
                     "textField": "c{}t".format(i)}
            cd = self._colDef(i, title)
            self._applyColDef(entry, cd)
            filterType = self._colFilterType(i, title)
            if filterType != "text":
                entry["filter"] = filterType
            if filterType == "range":
                entry["numberField"] = "c{}n".format(i)
            align = cd.get("align", "right" if filterType == "range" else None)
            if align is not None:
                entry["align"] = align
            if cd.get("headerWrap", self.headerWrap):
                entry["headerWrap"] = True
            spec.append(entry)
        return spec

    def _rangeCols(self):
        "set of column indices that use a numeric range filter"
        return {i for i, title in enumerate(self._colTitles())
                if self._colFilterType(i, title) == "range"}

    def _rowData(self, row, rowId, rangeCols):
        "build the Tabulator data object for one row"
        data = {"_id": rowId}
        for i, cell in enumerate(row.row):
            data["c{}".format(i)] = _cellHtml(cell)
            data["c{}s".format(i)] = _cellSortKey(cell)
            data["c{}t".format(i)] = _cellText(cell)
            if i in rangeCols:
                data["c{}n".format(i)] = _cellNumber(cell)
        if row.cssRowClass is not None:
            data["_cls"] = row.cssRowClass
        return data

    def _tableData(self):
        rangeCols = self._rangeCols()
        return [self._rowData(row, rowId, rangeCols)
                for rowId, row in enumerate(self.rows)]

    def _jsonEmbed(self, obj):
        "serialize obj as JSON safe to embed in a <script> element"
        return json.dumps(obj).replace("</", "<\\/")

    def _buildScript(self):
        "the per-page Tabulator initialization script"
        opts = {"globalSearch": self.globalSearch,
                "headerFilters": self.headerFilters,
                "layout": self.layout,
                "extra": self.tabulatorOptions or {}}
        parts = [_dynamicScriptHelpers,
                 "var _colSpec = {};".format(self._jsonEmbed(self._colSpec())),
                 "var _tableData = {};".format(self._jsonEmbed(self._tableData())),
                 "var _opts = {};".format(self._jsonEmbed(opts)),
                 _dynamicInitScript]
        return "\n".join(parts)

    def _addSearchBar(self, pg):
        if not self.globalSearch:
            return
        pg.add('<div id="dirSearchBar">')
        pg.add('Search: <input id="dirSearch" type="text" '
               'oninput="_dirGlobalSearch()" placeholder="search all columns">')
        pg.add('</div>')

    def _writeDirPage(self, outDir):
        headExtra = '<link href="{}" rel="stylesheet">\n<script src="{}"></script>'.format(
            _tabulatorCssUrl(self.tabulatorVersion), _tabulatorJsUrl(self.tabulatorVersion))
        pg = HtmlPage(title=self.title, headExtra=headExtra, inStyle=_dynamicStyle)
        if self.title:
            pg.h3(self.title)
        if self.pageDesc is not None:
            pg.add(self.pageDesc)
        self._addSearchBar(pg)
        pg.add('<div id="dirTable"></div>')
        pg.add('<script>')
        pg.add(self._buildScript())
        pg.add('</script>')
        pg.writeFile(os.path.join(outDir, "dir.html"))

    def write(self, outDir):
        fileOps.ensureDir(outDir)
        frame = self._mkFrame("dir.html", self.title, self.dirPercent, self.below)
        frame.writeFile(os.path.join(outDir, "index.html"))
        self._writeDirPage(outDir)


# Per-page init logic that consumes the _colSpec/_tableData/_opts globals set
# above it.  Kept as a static block since it contains only structural code.
_dynamicInitScript = """
var _columns = _colSpec.map(function(c) {
    var col = {title: c.title, field: c.field, formatter: "html",
               sorter: _keySort, sorterParams: {field: c.sortField}};
    if (_opts.headerFilters && c.filter !== "none") {
        if (c.filter === "range") {
            col.headerFilter = _rangeEditor;
            col.headerFilterFunc = _rangeFilter;
            col.headerFilterFuncParams = {field: c.numberField};
            col.headerFilterEmptyCheck = _rangeEmpty;
        } else {
            col.headerFilter = "input";
            col.headerFilterFunc = _colFilter;
            col.headerFilterFuncParams = {field: c.textField};
        }
    }
    if (c.wrap) col.cssClass = "dirWrap";
    if (c.headerWrap) col.headerWordWrap = true;
    if ("align" in c) { col.hozAlign = c.align; col.headerHozAlign = c.align; }
    if ("width" in c) col.width = c.width;       // fixed; does not flex
    if ("minWidth" in c) col.minWidth = c.minWidth;
    if ("grow" in c) col.widthGrow = c.grow;
    if ("shrink" in c) col.widthShrink = c.shrink;
    return col;
});
var _currentId = null;
var _config = {data: _tableData, columns: _columns, layout: _opts.layout,
               height: "100%", index: "_id",
               rowFormatter: function(row) {
                   var el = row.getElement();
                   var data = row.getData();
                   if (data._cls) el.classList.add(data._cls);
                   if (data._id === _currentId) {
                       el.classList.add("dirCurrent");
                   } else {
                       el.classList.remove("dirCurrent");
                   }
               }};
for (var k in _opts.extra) { _config[k] = _opts.extra[k]; }
var _dirTable = new Tabulator("#dirTable", _config);
// Tabulator 6 requires event callbacks to be registered via on(), not as
// constructor options.  Highlight the row whose link was last clicked.
function _dirSetCurrent(e, row) {
    if (!e.target.closest("a")) return;
    var prevId = _currentId;
    _currentId = row.getData()._id;
    if (prevId !== null) {
        var prev = _dirTable.getRow(prevId);
        if (prev) prev.reformat();
    }
    row.reformat();
}
_dirTable.on("rowClick", _dirSetCurrent);
var _searchFields = _colSpec.map(function(c) { return c.textField; });
function _dirGlobalSearch() {
    var v = document.getElementById("dirSearch").value.toLowerCase();
    if (v === "") {
        _dirTable.clearFilter();
    } else {
        _dirTable.setFilter(_anySearch, {fields: _searchFields, value: v});
    }
}
"""
