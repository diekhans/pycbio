# Copyright 2006-2012 Mark Diekhans
import os
from pycbio.sys import PycbioException


class HgConf(dict):
    """read hg.conf into this object.  Search order:
       1) supplied path
       2) HGDB_CONF env variable
       3) ~/.hg.conf
       user name is expanded"""
    def __init__(self, confFile=None):
        confFile = self.getHgConf(confFile=confFile)
        with open(confFile) as fh:
            for line in fh:
                self._parseLine(line)

    @classmethod
    def getHgConf(self, confFile=None):
        if confFile is None:
            confFile = os.getenv("HGDB_CONF")
        if confFile is None:
            confFile = "~/.hg.conf"
        confFile = os.path.expanduser(confFile)
        return confFile

    def _parseLine(self, line):
        line = line.strip()
        if (len(line) > 0) and not line.startswith("#"):
            i = line.find("=")
            if i < 0:
                raise PycbioException("expected name=value, got: " + line)
            self[line[0:i].strip()] = line[i + 1:].strip()

    _cache = {}

    @classmethod
    def obtain(cls, confFile=None):
        """factory for parsed hgconf files, caching results"""
        conf = cls._cache.get(confFile)
        if conf is None:
            conf = cls._cache[confFile] = HgConf(confFile)
        return conf
