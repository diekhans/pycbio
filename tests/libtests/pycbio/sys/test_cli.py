# Copyright 2006-2025 Mark Diekhans
"""Miscellaneous command line parsing operations tests"""
import sys
import os.path as osp
import argparse
import logging
import io
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
import pycbio.sys.testingSupport as ts
from pycbio.sys import cli, loggingOps

DEBUG = False

###
# logging support
###
def _removeLogHandlers(logger):
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

def _resetLogger():
    "set to default state before parsing command line"
    logger = logging.getLogger()
    _removeLogHandlers(logger)
    logger.setLevel(logging.WARNING)
    logging.basicConfig()

class MemoryLogHandler(logging.Handler):
    "capture log to memory"
    def __init__(self):
        super().__init__()
        self.stream = io.StringIO()

    def emit(self, record):
        log_entry = self.format(record)
        self.stream.write(log_entry + "\n")

    def get_logs(self):
        return self.stream.getvalue()

def _confTestLogger():
    "configure after using command line option to set level, dropping other handlers"
    logger = logging.getLogger()
    _removeLogHandlers(logger)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    memory_handler = MemoryLogHandler()
    memory_handler.setFormatter(formatter)
    logger.addHandler(memory_handler)
    return memory_handler


###
# test command line parsing with log setup
###
def _addTrekOpts(parser):
    parser.add_argument('--kirk', type=int)
    parser.add_argument('--spock', '-s', type=str)
    parser.add_argument('-m', '--mc-coy', dest='mc_coy', type=str)
    parser.add_argument('-u', dest='uhura', action='store_true')
    parser.add_argument('pike')

def _makeTrekParser():
    parser = argparse.ArgumentParser(description='to go where no one has gone before',
                                     exit_on_error=False)
    _addTrekOpts(parser)
    return parser

def _checkTrekOpts(opts, args, kirk, spock, mc_coy, uhura, pike):
    assert opts.kirk == kirk
    assert opts.spock == spock
    assert opts.mc_coy == mc_coy
    assert opts.uhura == uhura
    assert args.pike == pike
    assert "pike" not in opts
    assert "spock" not in args

def testGetOptsLong():
    _resetLogger()
    parser = _makeTrekParser()
    testargs = ('--log-level=DEBUG', '--kirk=10', '--spock=fred', 'foo')
    opts, args = cli.parseOptsArgsWithLogging(parser, testargs)
    _checkTrekOpts(opts, args, 10, 'fred', None, False, 'foo')
    memory_handler = _confTestLogger()
    logging.debug("testGetOptsLong")
    logging.info("testGetOptsLong")
    logging.warning("testGetOptsLong")
    logging.error("testGetOptsLong")
    assert memory_handler.get_logs() == ("root - DEBUG - testGetOptsLong\n"
                                         "root - INFO - testGetOptsLong\n"
                                         "root - WARNING - testGetOptsLong\n"
                                         "root - ERROR - testGetOptsLong\n")

def testGetOptsShort():
    _resetLogger()
    parser = _makeTrekParser()
    testargs = ('--log-level=INFO', '-s' 'fred', '-m', 'barney', '-u', 'baz')
    opts, args = cli.parseOptsArgsWithLogging(parser, testargs)
    _checkTrekOpts(opts, args, None, 'fred', 'barney', True, 'baz')
    memory_handler = _confTestLogger()
    logging.debug("testGetOptsShort")
    logging.info("testGetOptsShort")
    logging.warning("testGetOptsShort")
    assert memory_handler.get_logs() == ("root - INFO - testGetOptsShort\n"
                                         "root - WARNING - testGetOptsShort\n")

def testParseOptsArgs():
    parser = _makeTrekParser()
    testargs = ('-s' 'fred', '-m', 'barney', '-u', 'baz')
    opts, args = cli.parseOptsArgsWithLogging(parser, testargs)
    _checkTrekOpts(opts, args, None, 'fred', 'barney', True, 'baz')

def testParseSubcommand():
    # standard add all subcommand arguments up front
    parser = argparse.ArgumentParser(description='subspace communication',
                                     exit_on_error=False)
    parser.add_argument("--star-fleet", action="store_true")
    subparsers = parser.add_subparsers(dest='craft', required=True)
    shuttle_parser = subparsers.add_parser('shuttle', help='Shuttle craft')
    _addTrekOpts(shuttle_parser)

    testargs = ('--log-level=INFO', 'shuttle', '-s', 'fred', '-m', 'barney', '-u', 'baz')
    opts, args = cli.parseOptsArgsWithLogging(parser, testargs)
    assert args.craft == "shuttle"
    _checkTrekOpts(opts, args, None, 'fred', 'barney', True, 'baz')
    assert not opts.star_fleet

    memory_handler = _confTestLogger()
    logging.debug("testParseSubcommand")
    logging.info("testParseSubcommand")
    logging.warning("testParseSubcommand")
    logging.error("testParseSubcommand")
    assert memory_handler.get_logs() == ("root - INFO - testParseSubcommand\n"
                                         "root - WARNING - testParseSubcommand\n"
                                         "root - ERROR - testParseSubcommand\n")

def testParseSubcommandTwoPass():
    _resetLogger()
    # parse to find subcommand, then add arguments
    parser = argparse.ArgumentParser(description='subspace communication',
                                     exit_on_error=False)
    loggingOps.addCmdOptions(parser)
    subparsers = parser.add_subparsers(dest='craft', required=True)
    shuttle_parser = subparsers.add_parser('shuttle', help='Shuttle craft')

    testargs = ('--log-level=INFO', 'shuttle', '-s', 'fred', '-m', 'barney', '-u', 'baz')

    args0, argv = parser.parse_known_args(testargs)
    assert args0.craft == "shuttle"

    _addTrekOpts(shuttle_parser)

    opts, args = cli.parseOptsArgsWithLogging(parser, testargs)
    _checkTrekOpts(opts, args, None, 'fred', 'barney', True, 'baz')
    memory_handler = _confTestLogger()
    logging.debug("testParseSubcommand")
    logging.info("testParseSubcommand")
    logging.warning("testParseSubcommand")
    logging.error("testParseSubcommand")
    assert memory_handler.get_logs() == ("root - INFO - testParseSubcommand\n"
                                         "root - WARNING - testParseSubcommand\n"
                                         "root - ERROR - testParseSubcommand\n")

###
# test command line error handling
###


#
# matches to cliTestProg output
#
_userCausedMsgExpect = (
    'UserCausedException: bad user\n'
    '  Caused by: RuntimeError: two caught\n'
    '    Caused by: ValueError: bad, bad value\n'
    'Specify --log-debug for details\n')
_userCausedStackExpectRe = (
    r'^Traceback.+cliTestProg.+ValueError: bad, bad value\n'
    r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
    r'.+UserCausedException: bad user' '\n$')
_bugMsgExpect = (
    'BugException: bad software\n'
    '  Caused by: RuntimeError: two caught\n'
    '    Caused by: ValueError: bad, bad value\n'
    'Specify --log-debug for details\n')
_bugStackExpectRe = (
    r'^Traceback.+cliTestProg.+ValueError: bad, bad value\n'
    r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
    r'.+BugException: bad software' '\n$')
_annoyMsgExpect = (
    'AnnoyingException: very annoying\n'
    '  Caused by: RuntimeError: two caught\n'
    '    Caused by: ValueError: bad, bad value\n'
    'Specify --log-debug for details\n')
_annoyStackExpectRe = (
    r'^Traceback.+cliTestProg.+ValueError: bad, bad value\n'
    r'.+the direct cause.+raise RuntimeError\("two caught"\) from ex'
    r'.+AnnoyingException: very annoying' '\n$')
_fileNotFoundMsgExpect = (
    'FileNotFoundError: /dev/fred/barney\n'
    'Specify --log-debug for details\n')
_newLineMsgExpect = (
    'UserCausedException: bad user\n'
    '  Caused by: RuntimeError: two caught\n'
    '    Caused by: ValueError: Space\n'
    'the final\n'
    'frontier\n')

def _runCmdHandlerTestProg(request, errorWrap, *, errorClass=None,
                           printStackFilter=None, sysExit=None,
                           debugLog=False):
    cmd = [sys.executable, osp.join(ts.get_test_dir(request), "bin/cliTestProg")]
    if errorClass is not None:
        cmd.append("--error-class=" + errorClass)
    if printStackFilter is not None:
        cmd.append("--print-stack-filter=" + printStackFilter)
    if debugLog:
        cmd.append("--log-level=DEBUG")
    if sysExit is not None:
        cmd.append(f"--system-exit={sysExit}")
    cmd.append(errorWrap)
    try:
        if DEBUG:
            print("DEBUG run:", ' '.join(cmd), file=sys.stderr)
        pipettor.run(cmd)
        return (0, None)
    except pipettor.ProcessException as ex:
        if DEBUG:
            print("DEBUG err:", ex.stderr, file=sys.stderr)
        return ex.returncode, ex.stderr

def testCmdHanderOkay(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_wrap', errorClass='no_error')
    assert stderr is None
    assert returncode == 0

def testCmdHanderUser(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack')
    assert stderr == _userCausedMsgExpect
    assert returncode == 1

def testCmdHanderUserStack(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack', debugLog=True)
    ts.assert_regex_dotall(stderr, _userCausedStackExpectRe)
    assert returncode == 1

def testCmdHanderBug(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack')
    ts.assert_regex_dotall(stderr, _bugStackExpectRe)
    assert returncode == 1

def testCmdHanderNoStackExcepts(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack_excepts')
    assert stderr == _annoyMsgExpect
    assert returncode == 1

def testCmdHanderFileNotFound(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_wrap', errorClass='file_not_found')
    assert stderr == _fileNotFoundMsgExpect
    assert returncode == 1

def testCmdHanderFilterTrue(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack', printStackFilter="True")
    ts.assert_regex_dotall(stderr, _bugStackExpectRe)
    assert returncode == 1

def testCmdHanderFilterTrue2(request):
    # force even with NoStackError
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack', printStackFilter="True")
    ts.assert_regex_dotall(stderr, _userCausedStackExpectRe)
    assert returncode == 1

def testCmdHanderFilterFalse(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack', printStackFilter="False")
    assert stderr == _bugMsgExpect
    assert returncode == 1

def testCmdHanderFilterNone(request):
    # all through to default handling
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack', printStackFilter="None")
    ts.assert_regex_dotall(stderr, _bugStackExpectRe)
    assert returncode == 1

def testCmdHanderFilterNone2(request):
    # all through to default handling NoStackError
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack', printStackFilter="None")
    assert stderr == _userCausedMsgExpect
    assert returncode == 1

def testCmdHanderNewlineMsg(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack',
                                                errorClass='new_line_msg')
    ts.assert_regex_dotall(stderr, _newLineMsgExpect)
    assert returncode == 1

def testCmdHanderSysExit0(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack',
                                                sysExit=0)
    assert stderr is None
    assert returncode == 0

def testCmdHanderSysExit100(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack',
                                                sysExit=100)
    assert stderr == ""
    assert returncode == 100
