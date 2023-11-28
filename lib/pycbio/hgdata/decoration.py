# Copyright 2006-2023 Mark Diekhans
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

class Decoration(Bed):
    """Create BED decorators, which are BED 12 records with extra fields.

    If blocks are omitted, as single block for the range is created.
    If glyph is note None or Glyph.NA, then style is glyph, otherwise the style is block.

    see kent/src/hg/lib/decoration.as
    """
    def __init__(self, chrom, chromStart, chromEnd, name,
                 decoratedItemName, decoratedItemStart, decoratedItemEnd,
                 *, strand=None, itemRgb=None, blocks=None,
                 glyph=None, fillColor=None, extraCols=None):
        decoratedItem = f"{chrom}:{decoratedItemStart}-{decoratedItemEnd}:{decoratedItemName}"
        if (glyph is None) or (glyph is Glyph.NA):
            style = Style.block
            glyph = Glyph.NA
        else:
            style = Style.glyph
            glyph = Glyph(glyph)
        if blocks is None:
            blocks = [BedBlock(chromStart, chromEnd)]
        if itemRgb is None:
            itemRgb = "0,0,0"
        if fillColor is None:
            fillColor = itemRgb
        elif isinstance(fillColor, Color):
            fillColor = fillColor.toRgba8Str()
        decoExtraCols = [decoratedItem, str(style), fillColor, str(glyph)]
        if extraCols is not None:
            decoExtraCols += extraCols
        super(Decoration, self).__init__(chrom, chromStart, chromEnd, name=name, score=0, strand=strand,
                                         thickStart=chromStart, thickEnd=chromEnd, itemRgb=itemRgb, blocks=blocks,
                                         extraCols=decoExtraCols, numStdCols=12)
