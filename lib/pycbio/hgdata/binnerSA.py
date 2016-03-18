# Copyright 2006-2012 Mark Diekhans
""" Version of Binner class that works with sqlalchemy
"""
from .rangeFinder import Binner
from sqlalchemy import and_, or_


class BinnerSA(Binner):
    """generate sqlalchemy query to find overlapping ranges using bin numbers"""
    @staticmethod
    def getOverlappingSqlExpr(seqCol, binCol, startCol, endCol, seq, start, end):
        """General sqlalchemy experssion to select for overlaps with the specified range. Columns
        are SA column objects.  Returns an and__ object"""
        # build bin parts
        parts = []
        for bins in Binner.getOverlappingBins(start, end):
            if bins[0] == bins[1]:
                parts.append(binCol == bins[0])
            else:
                parts.append(and_(binCol >= bins[0], binCol <= bins[1]))
        return and_(seqCol == seq, startCol < end, endCol > start, or_(*parts))
