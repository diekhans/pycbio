from pycbio.tsv.TSVTable import TSVTable
from pycbio.tsv.TSVRow import TSVRow
from pycbio.hgdata.AutoSql import strArrayType
from pycbio.sys.Enumeration import Enumeration

class GeneCheckDetails(TSVRow):
    """Object wrapper for one record from the gene-check program details output """

def parseFeature(val):
    "feature is an int or blank"
    if isinstance(val, str):
        return -1
    else:
        return int(val)

typeMap = {"feature": parseFeature,
           "problem": intern}


class GeneCheckDetailsTbl(TSVTable):
    """Table of GeneCheckDetails objects loaded from a TSV.    """
    
    def __init__(self, fileName):
        TSVTable.__init__(self, fileName, rowClass=GeneCheckDetails,
                          typeMap=typeMap, multiKeyCols="id")
        
