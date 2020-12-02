# Copyright 2018-2018 Mark Diekhans
"""Parsing of NCBI AGP files.
"""
from pycbio.hgdata.coords import Coords
from pycbio.sys import fileOps, PycbioException


class AgpException(PycbioException):
    def __init__(self, message, agpFile=None, lineNum=None, line=None):
        msg = ""
        if agpFile is not None:
            msg += agpFile + ":"
        if lineNum is not None:
            msg += str(lineNum) + ": "
        msg += message
        if line is not None:
            msg += ": " + line
        super(AgpException, self).__init__(msg)


class Agp(object):
    """NCBI AGP file parser.
    https://www.ncbi.nlm.nih.gov/assembly/agp/AGP_Specification/
    """

    class Record(object):
        __slots__ = ("object", "part_number", "component_type")

        def __init__(self, object, part_number, component_type):
            self.object = object
            self.part_number = part_number
            self.component_type = component_type

        def format(self, oneBased=False):
            inc = 1 if oneBased else 0
            return "\t".join([self.object.name, str(self.object.start + inc), str(self.object.end), str(self.part_number), str(self.component_type)])

        def __str__(self):
            return self.format()

        @property
        def isBlock(self):
            return self.component_type not in "NU"

        @property
        def isGap(self):
            return self.component_type in "NU"

    class Block(Record):
        __slots__ = ("component",)

        def __init__(self, object, part_number, component_type, component):
            super(Agp.Block, self).__init__(object, part_number, component_type)
            self.component = component  # orientation in strand

        def format(self, oneBased=False):
            inc = 1 if oneBased else 0
            return super(Agp.Block, self).format(oneBased) + "\t" + "\t".join([self.component.name, str(self.component.start + inc), str(self.component.end), self.component.strand])

        def __str__(self):
            return self.format()

    class Gap(Record):
        __slots__ = ("gap_length", "gap_type", "linkage", "evidence")

        def __init__(self, object, part_number, component_type, gap_length, gap_type, linkage, evidence):
            super(Agp.Gap, self).__init__(object, part_number, component_type)
            self.gap_length = int(gap_length)
            self.gap_type = gap_type
            self.linkage = linkage
            self.evidence = evidence

        def format(self, oneBased=False):
            return super(Agp.Gap, self).format(oneBased) + "\t" + "\t".join([str(self.gap_length), self.gap_type, self.linkage, self.evidence])

        def __str__(self):
            return self.format()

    def __init__(self, agpFile):
        self.agpFile = agpFile
        self.agpVersion = None
        self.recs = []
        with fileOps.opengz(agpFile) as fh:
            self._parseLines(fh)

    def _parseLines(self, fh):
        lineNum = 0
        for line in fileOps.iterLines(fh):
            lineNum += 1
            try:
                self._parseLine(line)
            except Exception as ex:
                raise AgpException(str(ex), fh.name, lineNum, line) from ex

    def _parseLine(self, line):
        if line.startswith("##agp-version"):
            self._parseAgpVersion(line)
        elif line.startswith("#") or (len(line) == 0):
            pass
        else:
            self._parseRow(line)

    def _parseAgpVersion(self, line):
        parts = line.split()
        if len(parts) != 2:
            raise AgpException("invalid agp-version line")
        self.agpVersion = parts[1]

    def _parseRow(self, line):
        #              0          1          2          3              4             5             6             7            8
        # Format: object object_beg object_end part_number component_type component_id component_beg component_end  orientation
        #   Gaps: object object_beg object_end part_number     N          gap_length   gap_type      linkage        evidence
        row = line.split('\t')
        if len(row) != 9:
            raise AgpException("invalid AGP row, expected 9 columns, got".format(len(row)))
        if row[4] not in "NU":
            self.recs.append(self._parseBlock(row))
        else:
            self.recs.append(self._parseGap(row))

    def _parseBlock(self, row):
        return self.Block(Coords(row[0], int(row[1]) - 1, int(row[2]), strand='+'),
                          int(row[3]), row[4],
                          Coords(row[5], int(row[6]) - 1, int(row[7]), strand=('-' if row[8] == '-' else '+')))

    def _parseGap(self, row):
        return self.Gap(Coords(row[0], int(row[1]) - 1, int(row[2]), strand='+'),
                        int(row[3]), row[4], row[5], row[6], row[7], row[8])
