
## FIXME: needed for faster readings, but needs cleaned up, need reader/writer
## classes
from pycbio.sys import fileOps

class TabFile(list):
    """Class for reading tab-separated files.  Can be used standalone
       or read into rows of a specific type.
    """

   # FIXME add try and error msg with file/line num, move to row reader class; see fileOps.iterRows
    def _read(self, inFh):
        lineNum = 0
        for line in inFh:
            if not (self.hashAreComments and line.startswith('#')):
                    line=line[0:-1]
                    row = line.split("\t")
                    if self.rowClass:
                        self.append(self.rowClass(row))
                    else:
                        self.append(row)
                    lineNum += 1

    def __init__(self, fileName, rowClass=None, hashAreComments=False):
        """Read tab file into the object
        """
        self.fileName = fileName
        self.rowClass = rowClass
        reader = TabFileReader(self.fileName, hashAreComments)
        for row in reader:
            if self.rowClass:
                self.append(self.rowClass(row))
            else:
                self.append(row)

    @staticmethod
    def write(fh, row):
        """print a row (list or tuple) to a tab file."""
        cnt = 0;
        for col in row:
            if cnt > 0:
                fh.write("\t")
            fh.write(str(col))
            cnt += 1
        fh.write("\n")

class TabFileReader(object):
    def __init__(self, tabFile, hashAreComments=False):
        self.fh = fileOps.opengz(tabFile)
        self.hashAreComments = hashAreComments
        self.lineNum = 0

    def _readLine(self):
        try:
            self.lineNum += 1
            line = self.fh.readline()
            if (line == ""):
                return None
            else:
                line = line[0:-1]  # drop newline
                return line
        except Exception, e:
            # FIXME: loses traceback, need to close
            raise ValueError(self.fh.name + ":" + str(self.lineNum) + ": " + str(e), e)

    def __iter__(self):
        return self

    def next(self):
        while True:
            line = self._readLine()
            if line == None:
                self.fh.close();
                raise StopIteration
            if not (self.hashAreComments and line.startswith("#")):
                row = line.split("\t")
                return row

    def close(self):
        "early close"
        self.fh.close()
        self.fh = None
