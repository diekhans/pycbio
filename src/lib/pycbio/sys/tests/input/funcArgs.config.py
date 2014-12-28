import sys

class Barney(object):
    def __init__(self, f1, f2, f3, configPyFile):
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.configPyFile = configPyFile

def getConfig(f1, f2=None, f3=None):
    return Barney(f1, f2, f3, configPyFile)
