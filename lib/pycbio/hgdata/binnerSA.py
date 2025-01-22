# Copyright 2006-2025 Mark Diekhans
""" getOverlappingSqlExpr for SQLAlchemy
"""
from pycbio.hgdata import rangeFinder
from sqlalchemy import and_, or_


def getOverlappingSqlExprSA(seqCol, binCol, startCol, endCol, seq, start, end):
    """General sqlalchemy experssion to select for overlaps with the specified range. Columns
    are SA column objects.  Returns an and__ object"""
    # build bin parts
    parts = []
    for bins in rangeFinder.getOverlappingBins(start, end):
        if bins[0] == bins[1]:
            parts.append(binCol == bins[0])
        else:
            parts.append(and_(binCol >= bins[0], binCol <= bins[1]))
    return and_(seqCol == seq, startCol < end, endCol > start, or_(*parts))
