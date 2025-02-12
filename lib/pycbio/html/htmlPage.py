# Copyright 2006-2025 Mark Diekhans
""" Classes to handle creating HTML pages and fragments
"""

# FIXME: frameset kind of a hack
# FIXME: should build a tree, not a list of lines, but avoid a DOM.
# FIXME; probably some module to do all of this
# maybe: https://pypi.python.org/pypi/HtmlNode/0.1.8 (2013-10-27)
#        https://pypi.python.org/pypi/PyHTML/1.3.1 (2017-05-30, one release)
#        https://pypi.python.org/pypi/easyhtml/1.2.0 - no release info
#        https://pypi.python.org/pypi/htmlgen/1.0.0 (2018-02-21, MIT, little doc, looks cumbersome)
#        https://pypi.python.org/pypi/html/1.16 (no dev info
#         https://pypi.python.org/pypi/PyHTML/1.3.1 (2017-05-30)
# FIXME: add class TableCell


class HtmlPage(list):
    """ Object to assist in creating an HTML page.  Page is stored as a list
    of lines.  The lines will not contain any newlines"""

    def __init__(self, title=None, headExtra=None, inStyle=None, fragment=False, framesetAttrs=None):
        """Start a new page."""
        self.frameSet = (framesetAttrs is not None)
        self.title = title
        self.tableBodyCnt = 0
        if not fragment:
            self.append('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">')
            self.append("<html><head>")
            if title is not None:
                self.add("<title>" + title + "</title>")
            if headExtra is not None:
                self.add(headExtra)
            if inStyle is not None:
                self.append('<style type="text/css">')
                self.add(inStyle)
                self.append("</style>")
            self.append("</head>")
            if self.frameSet:
                self.append("<frameset " + " ".join(framesetAttrs) + ">")
            else:
                self.append("<body>")

    def add(self, line):
        """add a line or lines of HTML, ensuring no embedded new lines.
        If line is a list or tuple, each element is added"""
        if isinstance(line, list) or isinstance(line, tuple):
            for row in line:
                self.add(row)     # recurse!
        else:
            line = str(line)
            if line.find("\n") >= 0:
                self.extend(line.split("\n"))
            else:
                self.append(line)

    def header(self, hlevel, text):
        self.append("<" + hlevel + ">" + text + "</" + hlevel + ">")

    def h1(self, text):
        self.header("h1", text)

    def h2(self, text):
        self.header("h2", text)

    def h3(self, text):
        self.header("h3", text)

    def h4(self, text):
        self.header("h4", text)

    def h5(self, text):
        self.header("h5", text)

    def br(self, numBr=1):
        for i in range(numBr):
            self.append("<br>")

    def hr(self):
        self.append("<hr>")

    def span(self, text, id=None, hclasses=None):
        line = "<span"
        if id is not None:
            line += ' id="' + id + '"'
        if hclasses is not None:
            line += ' class="' + hclasses + '"'
        line += ">" + text + "</span>"
        self.append(line)

    def ul(self, rows):
        self.append("<ul>")
        for row in rows:
            self.add("<li> " + row)
        self.append("</ul>")

    def tableStart(self, caption=None, attrs=("border",), style=None, hclass=None):
        "start a table"
        tag = "<table"
        if attrs is not None:
            tag += " " + " ".join(attrs)
        if style is not None:
            tag += ' style="' + style + '"'
        if hclass is not None:
            tag += ' class="' + hclass + '"'
        tag += ">"
        self.append(tag)
        if caption is not None:
            self.append("<caption>{}</caption>".format(caption))
        self.tableBodyCnt = 0

    def _addTableRow(self, cell, row, hclasses=None):
        """ add a table row
        - cell = th or td
        - row, substituting &nbsp; for empty of None.  If a cell is
          a list or tuple. then the remain arguments become TH or TD
          attributes.
        - if hclasses is specified, it's a parallel sequence with
          class attr names for the cells, or none for no class.
        """
        # FIXME: drop hclasses, allow cell to be a more informative object
        hrow = "<tr>"
        i = 0
        for c in row:
            hrow += "<" + cell
            if (hclasses is not None) and (hclasses[i] is not None):
                hrow += ' class=\"' + hclasses[i] + '"'
            if isinstance(c, list) or isinstance(c, tuple):
                hrow += " " + " ".join(c[1:])
                c = c[0]
            hrow += ">"
            if (c is not None):
                c = str(c)
            if (c == "") or (c is None):
                hrow += "&nbsp;"
            else:
                hrow += c
            i += 1
        hrow += "</tr>"
        self.add(hrow)

    def tableHeader(self, row, hclasses=None):
        self.add("<thead>")
        self._addTableRow("th", row, hclasses)
        self.add("</thead>")

    def tableRow(self, row, hclasses=None):
        if self.tableBodyCnt == 0:
            self.add("<tbody")
        self.tableBodyCnt += 1
        self._addTableRow("td", row, hclasses)

    def tableEnd(self):
        if self.tableBodyCnt > 0:
            self.add("</tbody>")
        self.tableBodyCnt = 0
        self.append("</table>")

    def table(self, rows, header=None, caption=None):
        self.tableStart(caption=caption)
        if header is not None:
            self.tableHeader(header)
        for row in rows:
            self.tableRow(row)
        self.tableEnd

    def tsvTable(self, rows, cols=None, caption=None):
        self.tableStart(caption=caption)
        if (cols is not None):
            self.tableHeader(cols)
            for row in rows:
                self.tableRow(row.getColumns(cols))
        else:
            self.tableHeader(rows[0]._columns_)
            for row in rows:
                self.tableRow(row)
        self.tableEnd()

    def _pageClose(self):
        if self.frameSet:
            return "</frameset></html>"
        else:
            return "</body></html>"

    def __str__(self):
        return "\n".join(self + self._pageClose())

    def writeFile(self, fname):
        fh = open(fname, "w")
        try:
            for line in self:
                fh.write(line)
                fh.write("\n")
            fh.write(self._pageClose())
            fh.write("\n")
        finally:
            fh.close()

    def jsBackButton(self):
        self.append('<FORM><INPUT TYPE="Button" VALUE="Back" onClick="history.go(-1)"></form>')
