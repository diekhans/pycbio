# Copyright 2006-2025 Mark Diekhans
"""Miscellaneous command line parsing operations tests"""
import sys
import os.path as osp
import argparse
import pipettor
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.sys.testSupport import assert_regex_dotall, get_test_dir
from pycbio.sys import cli

DEBUG = False

class ArgParserNoExit(argparse.ArgumentParser):
    "raises exception rather than exit"
    def error(self, message):
        raise argparse.ArgumentError(None, message)

def makeTrekParser():
    parser = ArgParserNoExit(description='to go where no one has gone before')
    parser.add_argument('--kirk', type=int)
    parser.add_argument('--spock', '-s', type=str)
    parser.add_argument('-m', '--mc-coy', dest='mc_coy', type=str)
    parser.add_argument('-u', dest='uhura', action='store_true')
    parser.add_argument('pike')
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
    parser = makeTrekParser()
    testargs = ('--kirk=10', '--spock=fred', 'foo')
    args = parser.parse_args(testargs)
    opts, args = cli.splitOptionsArgs(parser, args)
    _checkTrekOpts(opts, args, 10, 'fred', None, False, 'foo')

def testGetOptsShort():
    parser = makeTrekParser()
    testargs = ('-s' 'fred', '-m', 'barney', '-u', 'baz')
    args = parser.parse_args(testargs)
    opts, args = cli.splitOptionsArgs(parser, args)
    _checkTrekOpts(opts, args, None, 'fred', 'barney', True, 'baz')

def testParseOptsArgs():
    parser = makeTrekParser()
    testargs = ('-s' 'fred', '-m', 'barney', '-u', 'baz')
    opts, args = cli.parseOptsArgs(parser, testargs)
    _checkTrekOpts(opts, args, None, 'fred', 'barney', True, 'baz')


##
# matches to cliTestProg output
##
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
    cmd = [sys.executable, osp.join(get_test_dir(request), "bin/cliTestProg")]
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
    assert_regex_dotall(stderr, _userCausedStackExpectRe)
    assert returncode == 1

def testCmdHanderBug(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack')
    assert_regex_dotall(stderr, _bugStackExpectRe)
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
    assert_regex_dotall(stderr, _bugStackExpectRe)
    assert returncode == 1

def testCmdHanderFilterTrue2(request):
    # force even with NoStackError
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack', printStackFilter="True")
    assert_regex_dotall(stderr, _userCausedStackExpectRe)
    assert returncode == 1

def testCmdHanderFilterFalse(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack', printStackFilter="False")
    assert stderr == _bugMsgExpect
    assert returncode == 1

def testCmdHanderFilterNone(request):
    # all through to default handling
    returncode, stderr = _runCmdHandlerTestProg(request, 'with_stack', printStackFilter="None")
    assert_regex_dotall(stderr, _bugStackExpectRe)
    assert returncode == 1

def testCmdHanderFilterNone2(request):
    # all through to default handling NoStackError
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack', printStackFilter="None")
    assert stderr == _userCausedMsgExpect
    assert returncode == 1

def testCmdHanderNewlineMsg(request):
    returncode, stderr = _runCmdHandlerTestProg(request, 'no_stack',
                                                errorClass='new_line_msg')
    assert_regex_dotall(stderr, _newLineMsgExpect)
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
