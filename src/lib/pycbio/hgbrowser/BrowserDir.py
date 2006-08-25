"""Create a frameset that that is a directory of locations in the genome
browser.
"""

from pycbio.hgbrowser.Coords import Coords
from pycbio.html.HtmlPage import HtmlPage
from pycbio.sys import fileOps

class Entry(list):
    "entry in directory"
    def __init__(self, coords, name, row):
        """Entry in directory, coords and name are used for sorting, row has
        formated cells"""
        self.coords = coords
        self.name = name
        self.extend(row)

class BrowserDir(object):
    """Create a frameset and collection of HTML pages that index one or more
    genome browsers.
    """

    def __init__(self, browserUrl, defaultDb, colNames=None, pageSize=50,
                 title=None, dirPercent=15, below=False, pageDesc=None,
                 initialTracks=None, style=None):
        "initialTrack is a dict, or none"
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
            l = ["&"]
            for t in initialTracks:
                l += t + "=" + initialTracks[t]
            self.initialTracksArgs = "&" + "&".join(l)
        self.style = style

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

    def mkAnchor(self, coords, text):
        return "<a href=\"" + self.mkUrl(coords) + "\" target=browser>" + text + "</a>"
        
    def add(self, coords, name=None, row=None):
        """add a row, linking to location, if row is None, construct one
        with link labeled with name.  If name is None, it's the location """
        if name == None:
            name = str(coords)
        if row == None:
            row = [self.mkAnchor(coords, name)]
        self.entries.append(Entry(coords, name, row))

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

    def _writeDirPage(self, outDir, pgEntries, pageNum, numPages):
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
        
        for entry in pgEntries:
            pg.tableRow(entry)
        pg.tableEnd()
        pg.add(pageLinks)

        dirFile = outDir + "/dir%d.html" % pageNum
        pg.writeFile(dirFile)

    def _writeDirPages(self, outDir):
        numPages = (len(self.entries)+self.pageSize-1)/self.pageSize

        if numPages == 0:
            # at least write an empty page
            self._writeDirPage(outDir, [], 1, 0)
            
        for pageNum in xrange(1,numPages+1):
            first = (pageNum-1) * self.pageSize
            last = first+(self.pageSize-1)
            pgEntries = self.entries[first:last]
            self._writeDirPage(outDir, pgEntries, pageNum, numPages)

    def write(self, outDir):
        fileOps.ensureDir(outDir)
        frame = self._mkFrame(self.title, self.dirPercent, self.below)
        frame.writeFile(outDir + "/index.html")
        self._writeDirPages(outDir)
