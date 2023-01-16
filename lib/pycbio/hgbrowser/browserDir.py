# Copyright 2006-2022 Mark Diekhans
"""Create a frameset that that is a directory of locations in the genome
browser.
"""
import copy
from urllib.parse import quote
from pycbio.html.htmlPage import HtmlPage
from pycbio.sys import fileOps

# FIXME: need to encode text
# FIXME: need to have ability set attributes on cells
#        this could be done by having full object model of rows.
# FIXME: cellClasses is also a pain, a Cell object would adress
# FIXME add altcounter thing form gencode/projs/mm39/mus-grch39-eval/bin/browserDirBuild
# maybe use https://pypi.org/project/htmlBuilder/

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

class Row:
    "Row in the table"
    __slots__ = ("row", "key", "cssRowClass", "cssCellClasses")

    def __init__(self, row, key=None, cssRowClass=None, cssCellClasses=None):
        """Row in the, key can be some value(s) used in sorting. The row
        should be HTML encoded.  If If cssCellClasses is not None, it should
        be an parallel vector with None or the class name for the
        corresponding cells"""
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

    def _toHtmlRowWithStyle(self):
        hrow = [self._mkRowStart()]
        for i in range(len(self.row)):
            if self.cssCellClasses[i] is not None:
                cell = '<td class="{}">{}'.format(self.cssCellClasses[i], str(self.row[i]))
            else:
                cell = "<td>{}".format(str(self.row[i]))
            hrow.append(cell)
        hrow.append("</tr>\n")
        return "".join(hrow)

    def _toHtmlRowSimple(self):
        hrow = [self._mkRowStart()]
        for c in self.row:
            hrow.append("<td>" + str(c))
        hrow.append("</tr>\n")
        return "".join(hrow)

    def toHtmlRow(self):
        if self.cssCellClasses is not None:
            return self._toHtmlRowWithStyle()
        else:
            return self._toHtmlRowSimple()

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

class BrowserDir:
    """Create a frameset and collection of HTML pages that index one or more
    genome browsers.
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
        """add an encoded row, row can be a list or an Row object"""
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

    def _mkFrame(self, title=None, dirPercent=15, below=False):
        """create frameset as a HtmlPage object"""

        if below:
            fsAttr = "rows={}%%,{}%%".format(100 - dirPercent, dirPercent)
        else:
            fsAttr = "cols={}%%,{}%%".format(dirPercent, 100 - dirPercent)
        pg = HtmlPage(title=title, framesetAttrs=(fsAttr,))

        fdir = '<frame name="dir" src="dir1.html">'
        fbr = '<frame name="browser" src="{}">'.format(self.mkDefaultUrl())
        if below:
            pg.add(fbr)
            pg.add(fdir)
        else:
            pg.add(fdir)
            pg.add(fbr)
        return pg

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

        dirFile = outDir + "/dir{}.html".format(pageNum)
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
        frame = self._mkFrame(self.title, self.dirPercent, self.below)
        frame.writeFile(outDir + "/index.html")
        self._writeDirPages(outDir)
