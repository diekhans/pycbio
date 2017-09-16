# global passedInModule is optional

from builtins import object
global configPyFile


class Fred(object):
    def __init__(self, n, configPyFile, passedInModule):
        self.f1 = n
        self.f2 = 2 * n
        self.configPyFile = configPyFile
        self.passedInModule = passedInModule


def getConfig(configPyFile):
    return Fred(10, configPyFile, globals().get("passedInModule"))
