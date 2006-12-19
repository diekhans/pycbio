
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
        try:
            for line in inFh:
                line=line[0:-1]
                row = line.split("\t")
                if self.rowClass:
                    self.append(self.rowClass(row))
                else:
                    self.append(row)
                lineNum += 1
        except Exception, e:
            # FIXME: loses traceback
            raise ValueError(inFh.name + ":" + str(lineNum) + ": " + str(e), e)

    def __init__(self, fileName, rowClass=None):
        """Read tab file into the object
        """
        self.fileName = fileName
        self.rowClass = rowClass
        inFh = fileOps.opengz(fileName)
        try:
            self._read(inFh)
        finally:
            inFh.close();


    def write(fh, row):
        """print a row (list or tuple) to a tab file."""
        cnt = 0;
        for col in row:
            if cnt > 0:
                fh.write("\t")
            fh.write(str(col))
            cnt += 1
        fh.write("\n")
    write = staticmethod(write)
