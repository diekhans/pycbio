def get_test_output_dir(request):
    """get the path to the output directory to use for this test, create if it doesn't exist"""
    outdir = osp.join(get_test_dir(request), "output")
    os.makedirs(outdir, exist_ok=True)
    return outdir

def get_test_output_file(request, ext=""):
    """Get path to the output file, using the current test id and append ext,
    which should contain a dot."""
    return osp.join(get_test_output_dir(request), get_test_id(request) + ext)

def get_test_expect_file(request, ext="", *, basename=None):
    """Get path to the expected file, using the current test id and append
    ext. If basename is used, it is instead of the test id, allowing share an
    expected file between multiple tests."""
    fname = basename if basename is not None else get_test_id(request)
    return osp.join("expected", fname + ext)

def _get_lines(fname):
    with open(fname) as fh:
        return fh.readlines()

def diff_test_files(exp_file, out_file):
    """diff expected and output files."""

    exp_lines = _get_lines(exp_file)
    out_lines = _get_lines(out_file)

    diffs = list(difflib.unified_diff(exp_lines, out_lines, exp_file, out_file))
    for diff in diffs:
        print(diff, end=' ', file=sys.stderr)

    if len(diffs) > 0:
        pytest.fail(f"test output differed  expected: '{exp_file}', got: '${out_file}'")

def diff_results_expected(request, ext="", *, basename=None):
    """diff expected and output files, with names computed from test id."""
    diff_test_files(get_test_expect_file(request, ext, basename=basename),
                    get_test_output_file(request, ext))

def _mk_err_spec(re_part, const_part):
    """Generate an exception matching regexp with a re part and an escaped static part
    This is manually used to generate error_sets.  Uses while developing tests."""
    pass

def _print_err_spec(setname, expect_spec, got_chain):
    """print out to use to manually edit test expected data"""
    print('@>', setname, file=sys.stderr)
    for got in got_chain:
        print(f"  {got[0].__name__}", repr(got[1]), file=sys.stderr)

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
