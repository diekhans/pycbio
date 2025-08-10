"""
Various functions to support testing with pytest

Copyright (c) 2024-2025, Mark Diekhans
Copyright (c) 2024-2025, The Regents of the University of California
"""
import pytest
import sys
import os
import os.path as osp
import errno
import threading
import re
import difflib
import io
import logging
import signal

# this keeps OS/X crash reporter from popping up on test error
def sigquit_handler(signum, frame):
    sys.exit(os.EX_SOFTWARE)


signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGABRT, sigquit_handler)

try:
    MAXFD = os.sysconf("SC_OPEN_MAX")
except ValueError:
    MAXFD = 256

def get_test_id(request):
    """request object is a standard parameter that can added to a test function"""
    return osp.basename(request.node.nodeid).replace("/", "_")

def get_test_dir(request):
    """Find test directory, which is were the current test_* file is at"""
    return os.path.dirname(str(request.node.fspath))

def get_test_input_file(request, fname):
    """Get a path to a file in the test input directory"""
    return osp.join(get_test_dir(request), "input", fname)

def get_test_output_dir(request):
    """get the path to the output directory to use for this test, create if it doesn't exist"""
    outdir = osp.join(get_test_dir(request), "output")
    os.makedirs(outdir, exist_ok=True)
    return outdir

def get_test_output_file(request, ext=""):
    """Get path to the output file, using the current test id and append ext,
    which should contain a dot."""
    return osp.join(get_test_output_dir(request), get_test_id(request) + ext)

def get_test_expect_dir(request):
    """get the path to the expected directory for this test"""
    expectdir = osp.join(get_test_dir(request), "expected")
    return expectdir

def get_test_expect_file(request, ext="", *, basename=None):
    """Get path to the expected file, using the current test id and append
    ext. If basename is used, it is instead of the test id, allowing share an
    expected file between multiple tests."""
    fname = basename if basename is not None else get_test_id(request)
    return osp.join(get_test_expect_dir(request), fname + ext)

def _get_lines(fname):
    with open(fname) as fh:
        return fh.readlines()

def _get_bytes(fname):
    with open(fname, "rb") as fh:
        return fh.read()

def must_exist(fname):
    if not osp.exists(fname):
        pytest.fail(f"file does not exist: {fname}")

def diff_test_files(exp_file, out_file):
    """diff expected and output files."""

    exp_lines = _get_lines(exp_file)
    out_lines = _get_lines(out_file)

    diffs = list(difflib.unified_diff(exp_lines, out_lines, exp_file, out_file))
    for diff in diffs:
        print(diff, end=' ', file=sys.stderr)

    if len(diffs) > 0:
        pytest.fail(f"test output differed  expected: '{exp_file}', got: '${out_file}'")

def diff_results_expected(request, ext="", *, expect_basename=None):
    """diff expected and output files, with names computed from test id."""
    diff_test_files(get_test_expect_file(request, ext, basename=expect_basename),
                    get_test_output_file(request, ext))

def diff_results_binary_expected(request, ext, expect_basename=None):
    """diff expected and output binary files.  If expect_basename is
    used, it is used insted of the test id to find the expected file,
    allowing share an expected file between multiple tests."""

    expFile = get_test_expect_file(request, ext, basename=expect_basename)
    expBytes = _get_bytes(expFile)

    outFile = get_test_output_file(request, ext)
    outBytes = _get_bytes(outFile)

    assert outBytes == expBytes

def _mk_err_spec(re_part, const_part):
    """Generate an exception matching regexp with a re part and an escaped static part
    This is manually used to generate error_sets.  Uses while developing tests."""
    pass

def _print_err_spec(setname, expect_spec, got_chain):
    """print out to use to manually edit test expected data"""
    print('@>', setname, file=sys.stderr)
    for got in got_chain:
        print(f"  {got[0].__name__}", repr(got[1]), file=sys.stderr)

def assert_regex_dotall(obj, expectRe, msg=None):
    """Fail if the str(obj) does not match expectRe operator, including `.' matching newlines"""
    assert re.match(expectRe, str(obj), re.DOTALL), \
        msg or "regexp '{}' does not match '{}'".format(expectRe, str(obj))

def get_num_running_threads():
    "get the number of threads that are running"
    n = 0
    for t in threading.enumerate():
        if t.is_alive():
            n += 1
    return n

def assert_single_thread():
    "fail if more than one thread is running"
    assert get_num_running_threads() == 1

def assert_no_child_procs():
    "fail if there are any running or zombie child process"
    try:
        s = os.waitpid(0, os.WNOHANG)
        pytest.fail(f"pending child processes or zombies: {s}")
    except OSError as ex:
        if ex.errno != errno.ECHILD:
            raise

def get_num_open_files():
    "count the number of open files"
    n = 0
    for fd in range(0, MAXFD):
        try:
            os.fstat(fd)
        except OSError:
            n += 1
    return MAXFD - n

def assert_num_open_files_same(prev_num_open):
    "assert that the number of open files has not changed"
    num_open = get_num_open_files()
    if num_open != prev_num_open:
        pytest.fail(f"number of open files changed, was {prev_num_open} now it is {num_open}")


class CheckRaisesCauses:
    """
    Validate exception chain against  [(exception, regex), ...].
    """
    def __init__(self, setname, expect_spec):
        self.setname = setname
        self.expect_spec = expect_spec

    def __enter__(self):
        return self

    @staticmethod
    def _build_got_chain(exc):
        "convert exception chain to a list to match"
        got = []
        while exc is not None:
            got.append((type(exc), str(exc)))
            exc = getattr(exc, "__cause__", None)
        return got

    @staticmethod
    def _check_except(got, expect):
        if got[0] != expect[0]:
            raise AssertionError(f"Expected exception of type `{expect[0].__name__}', got '{got[0].__name__}'")
        if not re.search(expect[1], got[1]):
            raise AssertionError(f"Expected message matching `{expect[1]}', got `{got[1]}'")

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Checks the raised exception and its causes against the provided list.
        """
        if exc_type is None:
            raise AssertionError("No exception was raised")
        got_chain = self._build_got_chain(exc_value)
        _print_err_spec(self.setname, self.expect_spec, got_chain)

        # check values before checking length to be easier to debug
        for got, expect in zip(got_chain, self.expect_spec[1]):
            self._check_except(got, expect)

        if len(self.expect_chain) != len(got_chain):
            raise AssertionError(f"Expect exception cause chain of {len(self.expect_chain)}, got {len(got_chain)}: {got_chain}")

        return True

class LoggerForTests():
    """test logger that logs to memory, each instance has a new logger"""
    def __init__(self, level=logging.DEBUG):
        self.logger = logging.getLogger(str(id(self)))
        self.logger.setLevel(level)
        self.__buffer = io.StringIO()
        self.logger.addHandler(logging.StreamHandler(self.__buffer))

    @property
    def data(self):
        return self.__buffer.getvalue()
