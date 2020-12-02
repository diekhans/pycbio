# Copyright 2006-2012 Mark Diekhans
"""Create a frameset that that is a directory of locations in the genome
browser.
"""
import copy
from urllib.parse import urlencode
from pycbio.html.htmlPage import HtmlPage
from pycbio.sys import fileOps

# FIXME: need to encode text
# FIXME: need to have ability set attributes on cells (e.g. heatmap)
#        this could be done by having full object model of rows.
# FIXME: cellClasses is also a pain, a Cell object would be
# FIXME: subrows is a hack, having full object model can make this go away
# FIXME add altcounter thing form gencode/projs/mm39/mus-grch39-eval/bin/browserDirBuild


defaultStyle = """
TABLE, TR, TH, TD {
    white-space: nowrap;
    border: solid;
    border-width: 1px;
    border-collapse: collapse;
}
"""


class SubRows(object):
    """Object used to specify a set of sub-rows.  Indicates number of columns
    occupied, which is need for laying out.
    """
    def __init__(self, numCols):
        self.numCols = numCols
        self.rows = []

    def addRow(self, row):
        assert(len(row) == self.numCols)
        self.rows.append(row)

    def getNumRows(self):
        return len(self.rows)

    def toTdRow(self, iRow):
        """return row of cells for the specified row, or one covering multiple
        columns if iRow exceeds the number of rows"""
        if iRow < len(self.rows):
            return "<td>" + "<td>".join([str(c) for c in self.rows[iRow]])
        elif self.numCols > 1:
            return "<td colspan={}>".format(self.numCols)
        else:
            return "<td>"


class Entry(object):
    "entry in directory"
    __slots__ = ("row", "key", "cssRowClass", "cssCellClasses", "subRowGroups")

    def __init__(self, row, key=None, cssRowClass=None, cssCellClasses=None, subRows=None):
        """Entry in directory, key can be some value(s) used in sorting. The
        row should be HTML encoded.  If subRows is not None, it should be a SubRow
        object or list of SubRow objects, used to produce row spanning rows for
        contained in this row.  If cssCellClasses is not None, it should be an parallel
        vector with wither None or the class name for the corresponding cells"""
        self.row = tuple(row)
        self.key = key
        self.cssRowClass = copy.copy(cssRowClass)
        self.cssCellClasses = copy.copy(cssCellClasses)
        self.subRowGroups = None
        if subRows is not None:
            if isinstance(subRows, SubRows):
                self.subRowGroups = [subRows]
            else:
                self.subRowGroups = subRows
        assert((self.cssCellClasses is None) or (len(self.cssCellClasses) == len(row)))
        assert((self.cssCellClasses is None) or (self.subRowGroups is None))  # can't have both yet

    def _numSubRowGroupCols(self):
        n = 0
        if self.subRowGroups is not None:
            for subRows in self.subRowGroups:
                n += subRows.numCols
        return n

    def _numSubRowGroupRows(self):
        n = 0
        if self.subRowGroups is not None:
            for subRows in self.subRowGroups:
                n = max(n, subRows.getNumRows())
        return n

    def numColumns(self):
        "compute number of columns that will be generated"
        return len(self.row) + self._numSubRowGroupCols()

    def _toHtmlRowWithSubRows(self):
        numSubRowRows = self._numSubRowGroupRows()
        hrow = ["<tr>"]
        td = "<td rowspan=\"{}\">".format(numSubRowRows)
        for c in self.row:
            hrow.append(td + str(c))
        if numSubRowRows > 0:
            for subRows in self.subRowGroups:
                hrow.append(subRows.toTdRow(0))
        hrow.append("</tr>\n")

        # remaining rows
        for iRow in range(1, numSubRowRows):
            hrow.append("<tr>\n")
            for subRows in self.subRowGroups:
                hrow.append(subRows.toTdRow(iRow))
            hrow.append("</tr>\n")
        return "".join(hrow)

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
        if self.subRowGroups is not None:
            return self._toHtmlRowWithSubRows()
        if self.cssCellClasses is not None:
            return self._toHtmlRowWithStyle()
        else:
            return self._toHtmlRowSimple()


class BrowserDir(object):
    """Create a frameset and collection of HTML pages that index one or more
    genome browsers.
    """

    def __init__(self, browserUrl, defaultDb, colNames=None, pageSize=50,
                 title=None, dirPercent=15, below=False, pageDesc=None,
                 tracks={}, initTracks={}, style=defaultStyle, numColumns=1, customTrackUrl=None):
        """The tracks arg is a dict of track name to setting, it is added to
        each URL and the initial setting of the frame. The initTracks arg is
        similar, however its only set in the initial frame and not added to
        each URL.
        A pageSize arg of None creates a single page. If numColumns is greater than 1
        create multi-column directories.
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
        self.numColumns = numColumns
        self.pageDesc = pageDesc
        self.entries = []
        self.style = style
        self.customTrackUrl = customTrackUrl
        self.trackArgs = tracks.copy()
        self.initTrackArgs = initTracks.copy()
        if customTrackUrl is not None:
            self.trackArgs["hgt.customText"] = self.customTrackUrl

    def mkUrl(self, coords, db=None, extra=None):
        """extract is a dict, the track arguments are added on if db defaultDb or None"""
        if db is None:
            db = self.defaultDb
        args = {"db": db,
                "position": str(coords)}
        if db == self.defaultDb:
            args.update(self.trackArgs)
        if extra is not None:
            args.update(extra)
        return "{}/cgi-bin/hgTracks?{}".format(self.browserUrl, urlencode(args))

    def mkDefaultUrl(self):
        return self.mkUrl("default", db=self.defaultDb, extra=self.initTrackArgs)

    def mkAnchor(self, coords, text=None, db=None, target="browser"):
        if text is None:
            text = str(coords)
        return "<a href=\"{}\" target={}>{}</a>".format(self.mkUrl(coords, db=db), target, text)

    def addRow(self, row, key=None, cssRowClass=None, cssCellClasses=None, subRows=None):
        """add an encoded row, row can be a list or an Entry object"""
        if not isinstance(row, Entry):
            row = Entry(row, key, cssRowClass, cssCellClasses, subRows)
        self.entries.append(row)

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
        self.entries.sort(key=keyFunc, reverse=reverse)

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

    def _padRows(self, pg, numPadRows, numColumns):
        if numColumns > 1:
            pr = "<tr colspan=\"{}\"></tr>".format(numColumns)
        else:
            pr = "<tr></tr>"
        for i in range(numPadRows):
            pg.add(pr)

    def _addPageRows(self, pg, pgEntries, numPadRows):
        """add one set of rows to the page.  In multi-column mode, this
        will be contained in a higher-level table"""
        pg.tableStart()
        if self.colNames is not None:
            pg.tableHeader(self.colNames)
        numColumns = None
        for ent in pgEntries:
            numColumns = ent.numColumns()  # better all be the same
            pg.add(ent.toHtmlRow())
        if numPadRows > 0:
            self._padRows(pg, numPadRows, numColumns)
        pg.tableEnd()

    def _addMultiColEntryTbl(self, pg, pgEntries):
        pg.tableStart()
        nEnts = len(pgEntries)
        rowsPerCol = nEnts // self.numColumns
        iEnt = 0
        pg.add("<tr>")
        for icol in range(self.numColumns):
            pg.add("<td>")
            if iEnt < nEnts - rowsPerCol:
                n = rowsPerCol
                np = 0
            else:
                n = nEnts - iEnt
                np = rowsPerCol - n
            self._addPageRows(pg, pgEntries[iEnt:iEnt + n], np)
            pg.add("</td>")
        pg.add("</tr>")
        pg.tableEnd()

    def _addEntryTbl(self, pg, pgEntries):
        if self.numColumns > 1:
            self._addMultiColEntryTbl(pg, pgEntries)
        else:
            self._addPageRows(pg, pgEntries, 0)

    def _writeDirPage(self, outDir, pgEntries, pageNum, numPages):
        title = "page {}".format(pageNum)
        if self.title:
            title += ": {}".format(self.title)
        pg = HtmlPage(title=title, inStyle=self.style)
        pg.h3(title)
        if self.pageDesc is not None:
            pg.add(self.pageDesc)
            pg.add("<br><br>")
        pg.add(self._getPageLinks(pageNum, numPages, False))
        self._addEntryTbl(pg, pgEntries)
        pg.add(self._getPageLinks(pageNum, numPages, True))

        dirFile = outDir + "/dir{}.html".format(pageNum)
        pg.writeFile(dirFile)

    def _writeDirPages(self, outDir):
        if len(self.entries) == 0:
            # at least write an empty page
            self._writeDirPage(outDir, [], 1, 0)
        elif self.pageSize is None:
            # single page
            self._writeDirPage(outDir, self.entries, 1, 1)
        else:
            # split
            numPages = (len(self.entries) + self.pageSize - 1) // self.pageSize
            for pageNum in range(1, numPages + 1):
                first = (pageNum - 1) * self.pageSize
                last = first + (self.pageSize - 1)
                pgEntries = self.entries[first:last]
                self._writeDirPage(outDir, pgEntries, pageNum, numPages)

    def write(self, outDir):
        fileOps.ensureDir(outDir)
        frame = self._mkFrame(self.title, self.dirPercent, self.below)
        frame.writeFile(outDir + "/index.html")
        self._writeDirPages(outDir)
