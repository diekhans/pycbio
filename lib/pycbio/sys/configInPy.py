"""
Configuration files written as python programs.
"""
import os
from types import FunctionType, ModuleType
from pycbio.sys import PycbioException

# FIXME: getFuncArgs could be handled by functools.partial much more elegantly

configPyFileVar = "configPyFile"


def _evalConfigFile(configPyFile, configEnv, extraEnv=None):
    "evaluate file and return environment"
    configEnv[configPyFileVar] = os.path.abspath(configPyFile)
    configEnv[include_config.__name__] = include_config
    if extraEnv is not None:
        configEnv.update(extraEnv)
    try:
        with open(configPyFile) as fh:
            exec(fh.read(), configEnv, configEnv)
    except Exception as ex:
        raise PycbioException("Error evaluating configuration file: {}".format(configPyFile)) from ex
    return configEnv


def include_config(inclPyFile, conflocals):
    callingPyFile = conflocals[configPyFileVar]
    if not os.path.isabs(inclPyFile):
        inclPyFile = os.path.normpath(os.path.join(os.path.dirname(callingPyFile), inclPyFile))
    try:
        conflocals.pop(configPyFileVar)
        _evalConfigFile(inclPyFile, conflocals)
    finally:
        conflocals[configPyFileVar] = callingPyFile


def evalConfigFunc(configPyFile, getFuncName="getConfig", getFuncArgs=[], getFuncKwargs={}, extraEnv=None):
    """Evaluate the specified configuration file and call the specified
    function (defaulting to getConfig()) define in the file.  The value of the
    call of this function is returned. This is useful for config files that
    need to construct complex objects.  Arguments and keyword arguments can be
    passed to this functions getFuncArgs, and getFuncKwargs.  The first
    argument is configPyFile, containing the configuration file name, which is
    also is set in the module globals before evaluation.  If specified, the
    dict extraEnv contents will be passed as a module globals.
    """
    configEnv = _evalConfigFile(configPyFile, configEnv=dict(), extraEnv=extraEnv)
    configFunc = configEnv.get(getFuncName)
    if configFunc is None:
        raise PycbioException("configuration script does not define function {}(): {} ".format(getFuncName, configPyFile))
    if not isinstance(configFunc, FunctionType):
        raise PycbioException("configuration script defines {}, however it is not a function: {}".format(getFuncName, configPyFile))
    getFuncArgs = [configPyFile] + list(getFuncArgs)
    try:
        return configFunc(*getFuncArgs, **getFuncKwargs)
    except Exception as ex:
        # FIXME really need traceback here
        raise PycbioException("Error from configuration function {}(): {}".format(getFuncName, configPyFile)) from ex


class Config(object):
    "configuration object"
    pass


def _includeField(key, value):
    return not (isinstance(value, ModuleType) or key.startswith('_'))


def evalConfigFile(configPyFile, extraEnv=None):
    """Evaluate the specified configuration file and return a object containing
    all values define in the module as fields.  This is useful for config
    files that just need to set values.  Builtins, modules, and fields
    starting with `_' are excluded.  A variable configPyFile, containing the
    configuration file name, is set in the module globals before
    evaluation. If specified, the dict extraEnv contents will be passed as a
    module globals and we be in the returned object.  This can be a way to specify
    defaults.

    A function `include_config(inclPyFile, conflocals)' will be defined in the
    environment.  The conflocals argument should be specified as locals().
    If inclPyFile is not absolute, it will found relative to configPyFile.
    The configPyFile variable is set to the absolute path to the included
    file while it is being evaluated.
    """
    configEnv = _evalConfigFile(configPyFile, configEnv=dict(), extraEnv=extraEnv)
    # construct object excluding some
    configObj = Config()
    for key in list(configEnv.keys()):
        if _includeField(key, configEnv[key]):
            setattr(configObj, key, configEnv[key])
    return configObj


__all__ = (evalConfigFunc.__name__, Config.__name__, evalConfigFile.__name__)
