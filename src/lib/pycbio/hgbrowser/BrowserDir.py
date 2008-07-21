"""Create a frameset that that is a directory of locations in the genome
browser.
"""

from pycbio.hgbrowser.Coords import Coords
from pycbio.html.HtmlPage import HtmlPage
from pycbio.sys import fileOps

class Entry(object):
    "entry in directory"
    def __init__(self, row, key=None, cssClass=None):
        """Entry in directory, key can be some value(s) used in sorting
        The row should be HTML encoded """
        self.row = list(row)
        self.key = key
        self.cssClass = cssClass

class BrowserDir(object):
    """Create a frameset and collection of HTML pages that index one or more
    genome browsers.
    """

    def __init__(self, browserUrl, defaultDb, colNames=None, pageSize=50,
                 title=None, dirPercent=15, below=False, pageDesc=None,
                 initialTracks=None, style=None):
        """initialTracks is a dict, or none; pageSize of None creates a single
        page"""
        self.browserUrl = browserUrl
        self.defaultDb = defaultDb
        self.colNames = colNames
        self.pageSize = pageSize
        self.title = title
        self.dirPercent = dirPercent
        self.below = below
        self.pageDesc = pageDesc
        self.entries = []
        self.initialTracksArgs = None
        if initialTracks != None:
            self.initialTracksArgs = self.__mkTracksArgs(initialTracks)
        else:
            self.initialTracksArgs = None
        self.style = style

    def __mkTracksArgs(self, initialTracks):
        l = []
        for t in initialTracks:
            l.append(t + "=" + initialTracks[t])
        return "&" + "&".join(l)
        
    def mkDefaultUrl(self):
        return self.browserUrl + "/cgi-bin/hgTracks?db=" + self.defaultDb + "&position=default"

    def mkUrl(self, coords):
        url = self.browserUrl + "/cgi-bin/hgTracks?db="
        if coords.db != None:
            url += coords.db
        else:
            url += self.defaultDb
        url += "&position=" + str(coords)
        return url

    def mkAnchor(self, coords, text=None):
        if text == None:
            text = str(coords)
        return "<a href=\"" + self.mkUrl(coords) + "\" target=browser>" + text + "</a>"
        
    def addRow(self, row, key=None, cssClass=None):
        """add an encoded row """
        self.entries.append(Entry(row, key, cssClass))

    def add(self, coords, name=None):
        """add a simple row, linking to location If name is None, it's the
        location """
        if name == None:
            name = str(coords)
        row = [self.mkAnchor(coords, name)]
        self.addRow(row, key=coords)

    def sort(self, cmpFunc=cmp):
        "sort by the key"
        self.sort(lambda a,b: cmpFunc(a.key, b.key))

    def _mkFrame(self, title=None, dirPercent=15, below=False):
        """create frameset as a HtmlPage object"""

        if below:
            fsAttr = "rows=%d%%,%d%%" % (100-dirPercent, dirPercent)
        else:
            fsAttr = "cols=%d%%,%d%%" % (dirPercent, 100-dirPercent)
        pg = HtmlPage(title=title, framesetAttrs=(fsAttr,))

        fdir = '<frame name="dir" src="dir1.html">'
        fbr = '<frame name="browser" src="%s">' % self.mkDefaultUrl()
        if below:
            pg.add(fbr)
            pg.add(fdir)
        else:
            pg.add(fdir)
            pg.add(fbr)
        return pg

    def _getPageLinks(self, pageNum, numPages):
        html = []
        # prev link
        if pageNum > 1:
            html.append("<a href=\"dir%d.html\">prev</a>" % (pageNum-1));
        else:
            html.append("prev")

        # page number links
        for p in xrange(1, numPages+1):
            if p != pageNum:
                html.append("<a href=\"dir%d.html\">%d</a>" % (p, p))
            else:
                html.append("[%d]" % p)

        # next link
        if pageNum < numPages:
            html.append("<a href=\"dir%d.html\">next</a>" % (pageNum+1))
        else:
            html.append("next")
        return ", ".join(html)

    def _writeDirPage(self, outDir, beginRow, endRow, pageNum, numPages):
        title = "page %d" % pageNum
        if self.title:
            title += ": " + self.title
        pg = HtmlPage(title=title, inStyle=self.style)
        pageLinks = self._getPageLinks(pageNum, numPages)
        pg.h3(title)
        if self.pageDesc != None:
            pg.add(self.pageDesc)
            pg.add("<br><br>")
        pg.add(pageLinks)
        
        pg.tableStart(style="white-space:nowrap;")
        if self.colNames != None:
            pg.tableHeader(self.colNames)
        
        for i in xrange(beginRow, endRow):
            pg.tableRow(self.entries[i].row)
        pg.tableEnd()
        pg.add(pageLinks)

        dirFile = outDir + "/dir%d.html" % pageNum
        pg.writeFile(dirFile)

    def _writeDirPages(self, outDir):
        if len(self.entries) == 0:
            # at least write an empty page
            self._writeDirPage(outDir, 0, 0, 1, 0)
        elif self.pageSize == None:
            # single page
            self._writeDirPage(outDir, 0, len(self.entries), 1, 1)
        else:
            # split
            numPages = (len(self.entries)+self.pageSize-1)/self.pageSize
            for pageNum in xrange(1,numPages+1):
                start = (pageNum-1) * self.pageSize
                end = start+self.pageSize
                if end > len(self.entries):
                    end = len(self.entries)
                if start < end:
                    self._writeDirPage(outDir, start, end, pageNum, numPages)

    def write(self, outDir):
        fileOps.ensureDir(outDir)
        frame = self._mkFrame(self.title, self.dirPercent, self.below)
        frame.writeFile(outDir + "/index.html")
        self._writeDirPages(outDir)
