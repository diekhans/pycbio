"""Template for creating a file-like class, mostly culled from StringIO.py"""

class FileLike:
    """"""
    def __notSupported(self, name):
        "raise an error about object not being supported"
        raise ValueError(name + " is not supported by " + str(self.__class__))

    def _checkOpen(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")

    def __init__(self):
        self.closed = False
    
    def __iter__(self):
        return self

    def next(self):
        """Iterator over file input lines"""
        if self.closed:
            raise StopIteration
        r = self.readline()
        if not r:
            raise StopIteration
        return r

    def close(self):
        """close file"""
        if not self.closed:
            self.closed = True

    def isatty(self):
        """Is this a tty-like device"""
        self._checkOpen()
        return False

    def seek(self, pos, mode = 0):
        """Set the file's current position."""
        _complain_ifclosed(self.closed)
        

    def tell(self):
        """Return the file's current position."""
        _complain_ifclosed(self.closed)
        return 0

    def read(self, n = -1):
        """Read at most size bytes from the file
        (less if the read hits EOF before obtaining size bytes).

        If the size argument is negative or omitted, read all data until EOF
        is reached. The bytes are returned as a string object. An empty
        string is returned when EOF is encountered immediately.
        """
        _complain_ifclosed(self.closed)
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        if n < 0:
            newpos = self.len
        else:
            newpos = min(self.pos+n, self.len)
        r = self.buf[self.pos:newpos]
        self.pos = newpos
        return r

    def readline(self, length=None):
        """Read one entire line from the file.

        A trailing newline character is kept in the string (but may be absent
        when a file ends with an incomplete line). If the size argument is
        present and non-negative, it is a maximum byte count (including the
        trailing newline) and an incomplete line may be returned.

        An empty string is returned only when EOF is encountered immediately.

        Note: Unlike stdio's fgets(), the returned string contains null
        characters ('\0') if they occurred in the input.
        """
        _complain_ifclosed(self.closed)
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        i = self.buf.find('\n', self.pos)
        if i < 0:
            newpos = self.len
        else:
            newpos = i+1
        if length is not None:
            if self.pos + length < newpos:
                newpos = self.pos + length
        r = self.buf[self.pos:newpos]
        self.pos = newpos
        return r

    def readlines(self, sizehint = 0):
        """Read until EOF using readline() and return a list containing the
        lines thus read.

        If the optional sizehint argument is present, instead of reading up
        to EOF, whole lines totalling approximately sizehint bytes (or more
        to accommodate a final whole line).
        """
        total = 0
        lines = []
        line = self.readline()
        while line:
            lines.append(line)
            total += len(line)
            if 0 < sizehint <= total:
                break
            line = self.readline()
        return lines

    def truncate(self, size=None):
        """Truncate the file's size.

        If the optional size argument is present, the file is truncated to
        (at most) that size. The size defaults to the current position.
        The current file position is not changed unless the position
        is beyond the new file size.

        If the specified size exceeds the file's current size, the
        file remains unchanged.
        """
        _complain_ifclosed(self.closed)
        if size is None:
            size = self.pos
        elif size < 0:
            raise IOError(EINVAL, "Negative size not allowed")
        elif size < self.pos:
            self.pos = size
        self.buf = self.getvalue()[:size]

    def write(self, s):
        """Write a string to the file.

        There is no return value.
        """
        _complain_ifclosed(self.closed)
        if not s: return
        # Force s to be a string or unicode
        if not isinstance(s, basestring):
            s = str(s)
        spos = self.pos
        slen = self.len
        if spos == slen:
            self.buflist.append(s)
            self.len = self.pos = spos + len(s)
            return
        if spos > slen:
            self.buflist.append('\0'*(spos - slen))
            slen = spos
        newpos = spos + len(s)
        if spos < slen:
            if self.buflist:
                self.buf += ''.join(self.buflist)
            self.buflist = [self.buf[:spos], s, self.buf[newpos:]]
            self.buf = ''
            if newpos > slen:
                slen = newpos
        else:
            self.buflist.append(s)
            slen = newpos
        self.len = slen
        self.pos = newpos

    def writelines(self, iterable):
        """Write a sequence of strings to the file. The sequence can be any
        iterable object producing strings, typically a list of strings. There
        is no return value.

        (The name is intended to match readlines(); writelines() does not add
        line separators.)
        """
        write = self.write
        for line in iterable:
            write(line)

    def flush(self):
        """Flush the internal buffer
        """
        _complain_ifclosed(self.closed)

    def getvalue(self):
        """
        Retrieve the entire contents of the "file" at any time before
        the StringIO object's close() method is called.

        The StringIO object can accept either Unicode or 8-bit strings,
        but mixing the two may take some care. If both are used, 8-bit
        strings that cannot be interpreted as 7-bit ASCII (that use the
        8th bit) will cause a UnicodeError to be raised when getvalue()
        is called.
        """
        if self.buflist:
            self.buf += ''.join(self.buflist)
            self.buflist = []
        return self.buf


# A little test suite

def test():
    import sys
    if sys.argv[1:]:
        file = sys.argv[1]
    else:
        file = '/etc/passwd'
    lines = open(file, 'r').readlines()
    text = open(file, 'r').read()
    f = StringIO()
    for line in lines[:-2]:
        f.write(line)
    f.writelines(lines[-2:])
    if f.getvalue() != text:
        raise RuntimeError, 'write failed'
    length = f.tell()
    print 'File length =', length
    f.seek(len(lines[0]))
    f.write(lines[1])
    f.seek(0)
    print 'First line =', repr(f.readline())
    print 'Position =', f.tell()
    line = f.readline()
    print 'Second line =', repr(line)
    f.seek(-len(line), 1)
    line2 = f.read(len(line))
    if line != line2:
        raise RuntimeError, 'bad result after seek back'
    f.seek(len(line2), 1)
    list = f.readlines()
    line = list[-1]
    f.seek(f.tell() - len(line))
    line2 = f.read()
    if line != line2:
        raise RuntimeError, 'bad result after seek back from EOF'
    print 'Read', len(list), 'more lines'
    print 'File length =', f.tell()
    if f.tell() != length:
        raise RuntimeError, 'bad length'
    f.close()

if __name__ == '__main__':
    test()
