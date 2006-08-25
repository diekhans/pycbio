
class TSVError(Exception):
    "Error from reading or parsing a TSV file"
    def __init__(self, msg, reader=None, cause=None):
        if (reader != None):
            msg = reader.fileName + ":" + str(reader.lineNum) + ": " + msg
        Exception.__init__(self, msg)


# FIXME: something here isn't right, like msg geting lost when pass to Exception
# so save it in object for now
class Damn(object):

    def __init__(self, msg, reader=None, cause=None):
        # line number is preserved if in cause
        self.fileName = None
        self.lineNum = None
        if type(cause) == TSVError:
            self.fileName = cause.fileName
            self.lineNum = cause.lineNum
        if reader != None:
            if self.fileName == None:
                self.fileName = reader.fileName
                self.lineNum = reader.lineNum

        # preserver cause messages
        if type(cause) == TSVError:
            msg = msg + ": " + cause.args[0]  # avoid str() do not dup file/line
        elif cause != None:
            msg = msg + ": " + str(cause)
        #FIXME: see comment at top of file
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        if self.fileName != None:
            return self.fileName + ":" + str(self.lineNum) + ": " + msg
        else:
            return  msg

        __repr__ =__str__
