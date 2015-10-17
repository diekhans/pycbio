"""
Configuration files written as python programs.
"""
import sys
from types import FunctionType, ModuleType
from pycbio.sys import PycbioException

def _evalConfigFile(configPyFile, extraEnv=None):
    "evaluate file and return environment"
    configEnv = {"configPyFile": configPyFile}
    if extraEnv is not None:
        configEnv.update(extraEnv)
    try:
        execfile(configPyFile, configEnv, configEnv)
    except:
        ei = sys.exc_info()
        raise PycbioException("Error evaluating configuration file: " + configPyFile, ei[0]), None, ei[2]
    return configEnv

# FIXME: now that configEnv has locals, we could get by varname.
# getFuncArgs could be handled by functools.partial much more elegently

def evalConfigFunc(configPyFile, getFuncName="getConfig", getFuncArgs=[], getFuncKwargs={}, extraEnv=None):
    """Evaluate the specified configuration file and call the specified function
    (defaulting to getConfig()) define in the file.  The value of the call of
    this function is returned. This is useful for config files that should
    construct complex objects.  Arguments and keyword arguments can be passed
    to this functions getFuncArgs, and getFuncKwargs.  A variable
    configPyFile, containing the configuration file name, is set in the module
    globals before evaluation.  If specified, the dict extraEnv contents will
    be passed as a module globals.
    """
    configEnv = _evalConfigFile(configPyFile, extraEnv)
    configFunc = configEnv.get(getFuncName)
    if configFunc is None:
        raise PycbioException("configuration script does not define function %s(): %s " % (getFuncName, configPyFile))
    if not isinstance(configFunc, FunctionType):
        raise PycbioException("configuration script defines %s, however it is not a function: %s " % (getFuncName, configPyFile))
    try:
        return configFunc(*getFuncArgs, **getFuncKwargs)
    except:
        ei = sys.exc_info()
        raise PycbioException("Error from configuration function %s(): %s " % (getFuncName, configPyFile), ei[1]), None, ei[2]

class Config(object):
    "configuration object"
    pass

def _includeField(key, value):
    return not (isinstance(value, ModuleType) or key.startswith('_'))

def evalConfigObj(configPyFile, extraEnv=None):
    """Evaluate the specified configuration file and return a object containing
    all values define in the module as fields.  This is useful for config
    files that just need to set values.  Builtins, modules, and fields
    starting with `_' are excluded.  A variable configPyFile, containing the
    configuration file name, is set in the module globals before
    evaluation. If specified, the dict extraEnv contents will be passed as a
    module globals and we be in the returned object.  This can be a way to specify
    defaults.
    """
    configEnv = _evalConfigFile(configPyFile, extraEnv)
    # construct object excluding some
    configObj = Config()
    for key in configEnv.keys():
        if _includeField(key, configEnv[key]):
            setattr(configObj, key, configEnv[key])
    return configObj
