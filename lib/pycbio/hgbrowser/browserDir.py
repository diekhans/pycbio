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
import functools
import importlib.resources
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


# client code for the dynamic pages, shipped as package data beside this module
# and inlined into each generated page
DYNAMIC_JS_FILE = "browserDirDynamic.js"

@functools.cache
def _dynamicJs():
    "the BrowserDirDynamic client code, read from the package data file"
    return importlib.resources.files(__package__).joinpath(DYNAMIC_JS_FILE).read_text()


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

def _sortKeyIsBlank(cell):
    "True if a cell's sort key is an empty/whitespace string"
    key = _cellSortKey(cell)
    return isinstance(key, str) and (key.strip() == "")

def _sortKeyBlankOrNumber(cell):
    "True if a cell's sort key is blank or numeric (numeric-sort detection)"
    return _sortKeyIsBlank(cell) or (_toNumber(_cellSortKey(cell)) is not None)

def _sortKeyIsNumber(cell):
    "True if a cell's sort key is a non-blank number"
    return (not _sortKeyIsBlank(cell)) and (_toNumber(_cellSortKey(cell)) is not None)

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
                 doc=None, tracks={}, initTracks={}, style=defaultStyle,
                 customTrackUrls=None, hubUrls=None):
        """The tracks arg is a dict of track name to setting, it is added to
        each URL and the initial setting of the frame. The initTracks arg is
        similar, however its only set in the initial frame and not added to
        each URL. customTrackUrls and hubUrls can be a string URL or list of URLs.
        doc is optional documentation shown on each directory page below the
        header; it may be an HTML string or a list of HTML strings, each
        rendered as its own paragraph.
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
        self.doc = doc
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
            fsAttr = 'rows="{}%,{}%"'.format(100 - dirPercent, dirPercent)
        else:
            fsAttr = 'cols="{}%,{}%"'.format(dirPercent, 100 - dirPercent)
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

    def _addDoc(self, pg):
        "add the optional documentation block below the header"
        if self.doc is None:
            return
        pg.add('<div class="dirDoc">')
        if isinstance(self.doc, str):
            pg.add(self.doc)
        else:
            for para in self.doc:
                pg.add("<p>{}</p>".format(para))
        pg.add('</div>')

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
        self._addDoc(pg)
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


_dynamicStyle = """
html, body { height: 100%; margin: 0; }
body { display: flex; flex-direction: column; font-family: sans-serif; }
#dirSearchBar { padding: 4px; flex: 0 0 auto; }
#dirSearch { width: 20em; }
#dirHelpBtn, #dirDescBtn { margin-left: 6px; width: 1.6em; height: 1.6em; line-height: 1;
              padding: 0; border: 1px solid #999; border-radius: 50%;
              background: #f0f0f0; font-weight: bold; cursor: pointer;
              vertical-align: middle; }
#dirTitle { margin: 4px; flex: 0 0 auto; }
/* The help stays IN THE FLOW and scrolls within its own box.  Floating it over the table
   was tried and does not work here: these pages are usually a frameset with the directory
   in a short frame, and an absolutely-positioned panel is clipped by that frame rather
   than floating above the window.  A capped, scrolling block gets the same benefit -- a
   long help cannot push the table away or run off the end -- with nothing to clip. */
#dirHelp { flex: 0 0 auto; max-width: 60em; max-height: 40vh; overflow-y: auto;
           margin: 0 4px 4px; padding: 2px 8px;
           border: 1px solid #ccc; background: #f8f8f8; }
#dirHelp ul { margin: 4px 0; padding-left: 1.4em; }
#dirHelp code { background: #eee; padding: 0 2px; }
#dirTable { flex: 1 1 auto; min-height: 0; }
.dirDoc { flex: 0 0 auto; margin: 0 4px 4px; }
/* The page description is BEHIND the ? beside the title, hidden until asked for.  Capping
   and scrolling it was not enough: on a short frame even a scrolled box is more of the
   window than the text deserves, and the table is what the page is for.  Shown, it is the
   same kind of panel as the filter help. */
.dirDesc { flex: 0 0 auto; max-width: 60em; max-height: 40vh; overflow-y: auto;
           margin: 0 4px 4px; padding: 2px 8px;
           border: 1px solid #ccc; background: #f8f8f8; }
/* a page description is usually prose plus a column glossary, and the browser's own
   spacing for a definition list is too loose to read as a list of columns */
.dirDesc h4 { margin: 8px 0 2px; }
.dirDesc dl { margin: 4px 0; }
.dirDesc dt { margin-top: 4px; }
.dirDesc dd { margin: 0 0 0 1.4em; }
.dirDesc code { background: #eee; padding: 0 2px; }
.tabulator-row.dirCurrent { background-color: #ffe08a !important;
                            box-shadow: inset 3px 0 0 #d97706; }
.tabulator-row .tabulator-cell.dirWrap,
.tabulator-row .tabulator-cell.dirWrapKeep { white-space: normal;
                                             overflow: visible;
                                             text-overflow: clip; }
/* dirWrap breaks anywhere it must, so no word can overflow the column. */
.tabulator-row .tabulator-cell.dirWrap { word-break: break-word; }
/* dirWrapKeep (breakWords=False) breaks only where the CONTENT offers a break -- a
   space, a <br>, a <wbr> -- and never inside a token.  A cell of coordinates needs
   this: broken anywhere, chr1:1,000-2,000 is split across two lines and reads as two
   positions.  The caller then chooses the break points, using &nbsp; where a space
   must not become one. */
.tabulator-row .tabulator-cell.dirWrapKeep { word-break: normal; overflow-wrap: normal; }
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
                 regexpFilters=True, filterHelp=None, colDefs=None,
                 tabulatorVersion=TABULATOR_VERSION,
                 tabulatorOptions=None, **kwargs):
        """globalSearch adds a search box that matches across all columns.
        headerFilters adds a per-column filter input under each header.
        headerWrap word-wraps the column-name titles of all columns (a column
        can override this with its own headerWrap in colDefs).  layout is the
        Tabulator layout mode; the default "fitColumns" makes the columns fill
        and resize with the window.

        regexpFilters makes the text filters (both the per-column ones and the
        global search) case-insensitive regular expressions rather than plain
        substrings; a pattern that does not compile, as happens while one is
        being typed, falls back to a substring match.  Either way, a help
        button by the search box describes the filtering; filterHelp is
        optional HTML appended to that description.

        colDefs is an optional dict giving per-column behavior, keyed by column
        name or zero-based index; each value is a dict with any of:
          - wrap:       True to word-wrap the cell content
          - breakWords: False to wrap ONLY where the content offers a break --
                        a space, a <br>, a <wbr> -- rather than anywhere a line
                        happens to end.  Use it for a cell of coordinates or
                        ids, which read as two values when split mid-token; the
                        caller then places the breaks, with &nbsp; where a space
                        must not become one.  Only meaningful with wrap.
          - fit:        True to size the column (client-side) to the widest of
                        its data and its header.  A fit column's header
                        word-wraps by default, so the header contributes only
                        its longest word to the width, not the whole title.
                        This is the default for columns that are not wrapped,
                        expanded, or explicitly sized; set fit=False to opt out.
                        A fit column is pinned to that width, unless it also
                        expands, in which case the width becomes its floor.
                        Either way the measured size is a MINIMUM: the layout
                        will not shrink the column below what its content
                        needs, which is what keeps a narrow window from
                        running one column's text over the next.
                        On a WRAP column, fit measures the longest LINE the
                        cell renders as (its content split at its <br>s) rather
                        than the whole cell, so the column is wide enough for
                        one line of it.  Worth setting with breakWords=False,
                        where a line cannot be broken to fit a narrower column.
          - expand:     True to make the column flex, absorbing extra space as
                        the window widens and giving it back as it narrows
                        (widthGrow with a small minWidth floor); use for the
                        column(s) that should soak up slack (e.g. locations).
                        Combine with fit to floor it at its content width; at
                        least one expanding column is needed for the table to
                        fill the window, since fit columns do not flex.
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
          - filter:     "text" (default, regexp or substring match, see
                        regexpFilters), "range" (numeric min/max filter), or
                        "none" (no header filter)
          - align:      data-cell horizontal alignment "left", "center", or
                        "right"; "range" columns default to "right"
          - headerAlign: header-title alignment (defaults to left, so a
                        right-aligned numeric column keeps a left header)
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
        self.regexpFilters = regexpFilters
        self.filterHelp = filterHelp
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
            if not cd.get("breakWords", True):
                entry["breakWords"] = False
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
            if "headerAlign" in cd:
                entry["headerAlign"] = cd["headerAlign"]
            if cd.get("expand"):
                entry.setdefault("grow", cd.get("grow", 1))
                entry.setdefault("minWidth", cd.get("minWidth", 60))
            if self._colNumericSort(i):
                entry["numericSort"] = True
            fit = self._colFit(cd, entry)
            if fit:
                entry["fit"] = True
            # fit/expand columns wrap their header by default so a wide title
            # does not force the column wide; only its longest word must fit
            wrapHdr = self.headerWrap or fit or bool(cd.get("expand"))
            if cd.get("headerWrap", wrapHdr):
                entry["headerWrap"] = True
            spec.append(entry)
        return spec

    def _colFit(self, cd, entry):
        """resolve size-to-content: an explicit colDefs fit wins; otherwise a
        column that is not wrapped, expanded, or explicitly sized defaults to
        fitting its content (so it does not flex and grow to fill the window)."""
        if "fit" in cd:
            return bool(cd["fit"]) and ("width" not in entry)
        if entry.get("expand"):
            return False
        return not any(k in entry for k in ("width", "minWidth", "grow", "wrap"))

    def _rangeCols(self):
        "set of column indices that use a numeric range filter"
        return {i for i, title in enumerate(self._colTitles())
                if self._colFilterType(i, title) == "range"}

    def _colNumericSort(self, i):
        "True if every non-blank sort key is numeric and at least one exists"
        cells = [row.row[i] for row in self.rows]
        if not all(_sortKeyBlankOrNumber(c) for c in cells):
            return False
        return any(_sortKeyIsNumber(c) for c in cells)

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
        "this page's data followed by the client code that builds the table"
        opts = {"globalSearch": self.globalSearch,
                "headerFilters": self.headerFilters,
                "regexpFilters": self.regexpFilters,
                "layout": self.layout,
                "extra": self.tabulatorOptions or {}}
        parts = ["var _colSpec = {};".format(self._jsonEmbed(self._colSpec())),
                 "var _tableData = {};".format(self._jsonEmbed(self._tableData())),
                 "var _opts = {};".format(self._jsonEmbed(opts)),
                 _dynamicJs()]
        return "\n".join(parts)

    def _addSearchBar(self, pg):
        "the search box and the button that reveals the filter help"
        if not (self.globalSearch or self.headerFilters):
            return
        pg.add('<div id="dirSearchBar">')
        if self.globalSearch:
            pg.add('Search: <input id="dirSearch" type="text" '
                   'oninput="_dirGlobalSearch()" placeholder="search all columns">')
        pg.add('<button id="dirHelpBtn" type="button" title="how filtering works" '
               'onclick="_dirToggleHelp()">?</button>')
        pg.add('</div>')
        self._addFilterHelp(pg)

    def _filterMatchDesc(self):
        "how a text filter treats what is typed into it"
        if self.regexpFilters:
            return ("What is typed is a case-insensitive regular expression, matched "
                    "anywhere in the value: <code>^chr1$</code> matches only the whole "
                    "value, <code>MIR1|MIR2</code> either of two.")
        else:
            return ("What is typed is case-insensitive text, matched anywhere in the "
                    "value.")

    def _filterHelpItems(self):
        "the standard description of how this page's filtering works"
        items = [self._filterMatchDesc()]
        if self.regexpFilters:
            items.append("To match everything <i>but</i> some value, negate it with a "
                         "look-ahead: <code>^(?!ok$).*</code> finds all values other "
                         "than <code>ok</code>.")
        if self.headerFilters:
            items.append("The box under a column name filters on that column alone.")
            if self._rangeCols():
                items.append("Numeric columns have <b>min</b>/<b>max</b> boxes instead; "
                             "fill in just one for an open-ended range.")
        if self.globalSearch:
            items.append("The <b>Search</b> box matches against all columns at once.")
        items.append("Filters combine: a row is shown only when it passes every one of them.")
        if self.regexpFilters:
            items.append("An expression that is not valid, as while it is still being typed, "
                         "matches as plain text instead.")
        return items

    def _addTitle(self, pg):
        """the title, carrying the ? that reveals the page description.  Beside the title
        because that is where a reader looks to find out what a page is, and because the
        other ? -- filtering -- belongs with the search box it explains."""
        if not self.title:
            return
        button = ('<button id="dirDescBtn" type="button" title="about this page" '
                  'onclick="_dirToggleDesc()">?</button>' if self.pageDesc is not None
                  else "")
        pg.add("<h3 id=\"dirTitle\">{}{}</h3>".format(self.title, button))

    def _addPageDesc(self, pg):
        """the caller's description, hidden until the ? beside the title is clicked.

        HIDDEN, not merely capped: it was emitted raw first, which left the table a
        sliver, then capped and scrolled, which still spent a quarter of a short frame on
        text that is read once.  The table is what the page is for."""
        if self.pageDesc is not None:
            pg.add('<div id="dirDesc" class="dirDesc" hidden>')
            pg.add(self.pageDesc)
            pg.add('</div>')

    def _addFilterHelp(self, pg):
        "the (initially hidden) filter-help block, with any caller-supplied HTML"
        pg.add('<div id="dirHelp" hidden>')
        pg.add("<ul>")
        for item in self._filterHelpItems():
            pg.add("<li>{}</li>".format(item))
        pg.add("</ul>")
        if self.filterHelp is not None:
            pg.add(self.filterHelp)
        pg.add("</div>")

    def _writeDirPage(self, outDir):
        headExtra = '<link href="{}" rel="stylesheet">\n<script src="{}"></script>'.format(
            _tabulatorCssUrl(self.tabulatorVersion), _tabulatorJsUrl(self.tabulatorVersion))
        pg = HtmlPage(title=self.title, headExtra=headExtra, inStyle=_dynamicStyle)
        self._addTitle(pg)
        self._addDoc(pg)
        self._addPageDesc(pg)
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
