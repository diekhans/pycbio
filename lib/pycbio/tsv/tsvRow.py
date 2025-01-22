# Copyright 2006-2025 Mark Diekhans

# FIXME: danger of dump, etc, methods conflicting with columns.  maybe
# a better convention to avoid collisions or make these functions rather
# than methods
# FIXME: need accessor functions for columns
# FIXME: need way to get raw row with Nones for sql
# FIXME: this could actually be a dict-like object since py3

def tsvRowToDict(row):
    """convert a TSV row to a dict"""
    return {col: getattr(row, col) for col in row._reader_.columns}


class TsvRow:
    "Row of a TSV where columns are fields."
    # n.b.: doesn't inherit from list, as this results in columns in two
    # places when they are stored as fields

    def __init__(self, reader, row):
        self._reader_ = reader
        for i in range(len(self._reader_.columns)):
            setattr(self, self._reader_.columns[i], row[i])

    def __getitem__(self, key):
        "access a column by string key or numeric index"
        if isinstance(key, int):
            return getattr(self, self._reader_.columns[key])
        else:
            return getattr(self, key)

    def __setitem__(self, key, val):
        "set a column by string key or numeric index"
        if isinstance(key, int):
            setattr(self, self._reader_.columns[key], val)
        else:
            setattr(self, key, val)

    def get(self, key, default=None):
        """Return the value for string key or numeric index, if key is in the
        dictionary, else default."""
        if isinstance(key, int):
            return getattr(self, self._reader_.columns[key]) if key < len(self._reader_.columns) else default
        else:
            return getattr(self, key, default)

    def __len__(self):
        return len(self._reader_.columns)

    def __iter__(self):
        for col in self._reader_.columns:
            yield getattr(self, col)

    def __contains__(self, key):
        return key in self._reader_.colMap

    def getRow(self):
        return self._reader_.formatRow(self)

    def __str__(self):
        return "\t".join(self.getRow())

    def __repr__(self):
        return str(self)

    def getColumns(self, colNames):
        """get a subset of the columns in the row as a list"""
        subRow = []
        for col in colNames:
            subRow.append(self[col])
        return subRow

    def write(self, fh):
        fh.write(str(self))
        fh.write("\n")

    def dump(self, fh):
        i = 0
        for col in self:
            if i > 0:
                fh.write("\t")
            fh.write(self._reader_.columns[i])
            fh.write(": ")
            fh.write(str(col))
            i += 1
        fh.write("\n")
