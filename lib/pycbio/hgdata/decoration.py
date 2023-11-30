# Copyright 2006-2023 Mark Diekhans
from pycbio import PycbioException
from pycbio.hgdata.bed import Bed, BedBlock
from pycbio.sys.symEnum import SymEnum
from pycbio.sys.color import Color

class Style(SymEnum):
    "style of decorated item"
    block = 0
    glyph = 1

class Glyph(SymEnum):
    "supported glyphs"
    NA = 0
    Circle = 1
    Square = 2
    Diamond = 3
    Triangle = 4
    InvTriangle = 5
    Octagon = 6
    Star = 7
    Pentagram = 8


DECO_NUM_STD_COLUMNS = 12 + 4

class Decoration(Bed):
    """Create BED decorators, which are BED 12 records with extra fields.

    If blocks are omitted, as single block for the range is created.
    If glyph is note None or Glyph.NA, then style is glyph, otherwise the style is block.

    see kent/src/hg/lib/decoration.as
    """
    __slots__ = ("decoratedItemName", "decoratedItemStart", "decoratedItemEnd", "decoratedItem",
                 "style", "fillColor", "glyph", "decoExtraCols")

    def __init__(self, chrom, chromStart, chromEnd, name,
                 decoratedItemName, decoratedItemStart, decoratedItemEnd,
                 *, strand=None, itemRgb=None, blocks=None,
                 glyph=None, fillColor=None, decoExtraCols=None):
        if blocks is None:
            blocks = [BedBlock(chromStart, chromEnd)]
        if itemRgb is None:
            itemRgb = "0,0,0"
        super(Decoration, self).__init__(chrom, chromStart, chromEnd, name=name, score=0, strand=strand,
                                         thickStart=chromStart, thickEnd=chromEnd, itemRgb=itemRgb, blocks=blocks,
                                         numStdCols=12)
        self.decoratedItemName = decoratedItemName
        self.decoratedItemStart = decoratedItemStart
        self.decoratedItemEnd = decoratedItemEnd
        self.decoExtraCols = decoExtraCols
        self.decoratedItem = f"{chrom}:{decoratedItemStart}-{decoratedItemEnd}:{decoratedItemName}"
        if (glyph is None) or (glyph is Glyph.NA):
            self.style = Style.block
            self.glyph = Glyph.NA
        else:
            self.style = Style.glyph
            self.glyph = Glyph(glyph)
        if fillColor is None:
            fillColor = itemRgb
        if isinstance(fillColor, Color):
            fillColor = fillColor.toRgba8Str()
        self.fillColor = fillColor

    @classmethod
    def parse(cls, row, numStdCols=None):
        raise PycbioException("Decoration.parse not implement")

    def toRow(self):
        row = super().toRow()
        row += [self.decoratedItem, str(self.style), self.fillColor,
                str(self.glyph)]
        if self.decoExtraCols is not None:
            row += list(self.decoExtraCols)
        return row
