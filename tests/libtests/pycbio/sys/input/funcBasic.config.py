# global passedInModule is optional


class Fred(object):
    def __init__(self, n, configPyFile, passedInModule):
        self.f1 = n
        self.f2 = 2 * n
        self.configPyFile = configPyFile
        self.passedInModule = passedInModule


def getConfig():
    global configPyFile
    return Fred(10, configPyFile, globals().get("passedInModule"))
