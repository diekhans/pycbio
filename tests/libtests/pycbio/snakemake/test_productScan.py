# Copyright 2006-2026 Mark Diekhans
"""tests of per-item product staleness and the scan stamp"""
import os
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.snakemake.productScan import ProductScan, outputs_current, env_flag


def _touch(path, mtime=None):
    "create a file, optionally with a specific mtime; returns the path as a str"
    path = str(path)
    with open(path, "w") as fh:
        fh.write("x\n")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


###
# outputs_current
###
def testOutputsCurrentAllNewer(tmp_path):
    inp = _touch(tmp_path / "in", 1000)
    out = _touch(tmp_path / "out", 2000)
    assert outputs_current([out], [inp])

def testOutputsCurrentSameMtime(tmp_path):
    "an output built in the same second as its input counts as current"
    inp = _touch(tmp_path / "in", 1000)
    out = _touch(tmp_path / "out", 1000)
    assert outputs_current([out], [inp])

def testOutputsCurrentMissingOutput(tmp_path):
    inp = _touch(tmp_path / "in", 1000)
    assert not outputs_current([str(tmp_path / "never-built")], [inp])

def testOutputsCurrentOlderOutput(tmp_path):
    inp = _touch(tmp_path / "in", 2000)
    out = _touch(tmp_path / "out", 1000)
    assert not outputs_current([out], [inp])

def testOutputsCurrentOldestOutputDecides(tmp_path):
    "one output rewritten by a partial run does not vouch for its siblings"
    inp = _touch(tmp_path / "in", 2000)
    fresh = _touch(tmp_path / "out1", 3000)
    stale = _touch(tmp_path / "out2", 1000)
    assert not outputs_current([fresh, stale], [inp])

def testOutputsCurrentMissingInputIgnored(tmp_path):
    "an absent input is a filter that does not apply, not an infinitely new input"
    out = _touch(tmp_path / "out", 1000)
    assert outputs_current([out], [str(tmp_path / "no-censat"), ])

def testOutputsCurrentNoInputs(tmp_path):
    out = _touch(tmp_path / "out", 1000)
    assert outputs_current([out], [])


###
# env_flag
###
def testEnvFlagUnset(monkeypatch):
    monkeypatch.delenv("PYCBIO_TEST_FLAG", raising=False)
    assert not env_flag("PYCBIO_TEST_FLAG")
    assert env_flag("PYCBIO_TEST_FLAG", default="1")

def testEnvFlagOff(monkeypatch):
    for value in ("0", "", "false", "no"):
        monkeypatch.setenv("PYCBIO_TEST_FLAG", value)
        assert not env_flag("PYCBIO_TEST_FLAG")

def testEnvFlagOn(monkeypatch):
    for value in ("1", "true", "yes", "anything"):
        monkeypatch.setenv("PYCBIO_TEST_FLAG", value)
        assert env_flag("PYCBIO_TEST_FLAG")


###
# ProductScan; a stage's products are <item>.out, with item "none" having none
###
def _mkScan(tmp_path, items=("a", "b"), *, watch=(), full_check=False, log=None,
            sentinel=True):
    "a scan of one stage, whose sentinel is created unless sentinel=False"
    path = str(tmp_path / "stage.done")
    if sentinel and not os.path.exists(path):
        _touch(path)
    return ProductScan(items=lambda: items, stamp=tmp_path / "scan.stamp",
                       sentinels=[path], watch=watch, full_check=full_check,
                       log=log), path

def _mkProducts(tmp_path):
    def products(item):
        return [None] if item == "none" else [str(tmp_path / (item + ".out"))]
    return products

def testNoStampIsFullScan(tmp_path):
    scan, _ = _mkScan(tmp_path)
    assert not scan.skip_scan
    assert scan.reason == "no scan stamp yet"

def testMissingSentinelIsFullScan(tmp_path):
    "a never-completed stage must not look finished"
    scan, sentinel = _mkScan(tmp_path)
    scan.record_if_clean()
    os.unlink(sentinel)
    scan2, _ = _mkScan(tmp_path, sentinel=False)
    assert not scan2.skip_scan
    assert scan2.reason == f"stage sentinel missing ({sentinel})"

def testFullCheckForcesScan(tmp_path):
    scan, _ = _mkScan(tmp_path)
    scan.record_if_clean()
    scan2, _ = _mkScan(tmp_path, full_check=True)
    assert not scan2.skip_scan
    assert scan2.reason == "full check requested"

def testPendingIsTheMissingProducts(tmp_path):
    products = _mkProducts(tmp_path)
    _touch(tmp_path / "a.out")
    scan, _ = _mkScan(tmp_path, items=("a", "b", "c"))
    work = scan.pending(products)
    assert work == [("b", [str(tmp_path / "b.out")]),
                    ("c", [str(tmp_path / "c.out")])]
    assert ProductScan.pending_products(work) == [str(tmp_path / "b.out"),
                                                  str(tmp_path / "c.out")]
    assert scan.found_work

def testPendingSkipsNoneProducts(tmp_path):
    "an item that cannot have a product is excluded, not reported as missing"
    scan, _ = _mkScan(tmp_path, items=("none",))
    assert scan.pending(_mkProducts(tmp_path)) == []
    assert not scan.found_work

def testPendingItemsOverride(tmp_path):
    scan, _ = _mkScan(tmp_path, items=("a", "b"))
    work = scan.pending(_mkProducts(tmp_path), items=("b",))
    assert work == [("b", [str(tmp_path / "b.out")])]

def _mkSources(tmp_path):
    "item -> what its product is built from, the shape pending() wants"
    return lambda item: [str(tmp_path / f"{item}.src")]

def testPendingWithSourcesRebuildsTheStale(tmp_path):
    "a product older than its source is pending, though it exists"
    _touch(tmp_path / "a.src", 2000)
    _touch(tmp_path / "a.out", 1000)
    _touch(tmp_path / "b.src", 1000)
    _touch(tmp_path / "b.out", 2000)
    scan, _ = _mkScan(tmp_path, items=("a", "b"))
    work = scan.pending(_mkProducts(tmp_path), sources=_mkSources(tmp_path))
    assert work == [("a", [str(tmp_path / "a.out")])]

def testPendingWithSourcesSameMtimeIsCurrent(tmp_path):
    "built in the same second as its source counts as current, as outputs_current has it"
    _touch(tmp_path / "a.src", 1000)
    _touch(tmp_path / "a.out", 1000)
    scan, _ = _mkScan(tmp_path, items=("a",))
    assert scan.pending(_mkProducts(tmp_path), sources=_mkSources(tmp_path)) == []

def testPendingWithSourcesMissingSourceIgnored(tmp_path):
    "a source that does not exist does not make its product rebuild forever"
    _touch(tmp_path / "a.out", 1000)
    scan, _ = _mkScan(tmp_path, items=("a",))
    assert scan.pending(_mkProducts(tmp_path), sources=_mkSources(tmp_path)) == []

def testPendingWithoutSourcesIgnoresMtime(tmp_path):
    "the old behaviour, for a stage whose products cannot go stale"
    _touch(tmp_path / "a.src", 2000)
    _touch(tmp_path / "a.out", 1000)
    scan, _ = _mkScan(tmp_path, items=("a",))
    assert scan.pending(_mkProducts(tmp_path)) == []

def testAllProductsIncludesBuiltAndSkipsNone(tmp_path):
    _touch(tmp_path / "a.out")
    scan, _ = _mkScan(tmp_path, items=("a", "b", "none"))
    assert scan.all_products(_mkProducts(tmp_path)) == [str(tmp_path / "a.out"),
                                                        str(tmp_path / "b.out")]

def testFoundWorkBlocksRecord(tmp_path):
    "a scan that found work never records itself as clean"
    scan, _ = _mkScan(tmp_path)
    scan.pending(_mkProducts(tmp_path))
    assert not scan.record_if_clean()
    assert not os.path.exists(tmp_path / "scan.stamp")

def testCleanScanRecordsStamp(tmp_path):
    products = _mkProducts(tmp_path)
    _touch(tmp_path / "a.out")
    _touch(tmp_path / "b.out")
    scan, _ = _mkScan(tmp_path)
    assert scan.pending(products) == []
    assert scan.record_if_clean()
    assert open(tmp_path / "scan.stamp").read() == "a\nb\n"

def testRecordedStampTakesTheFastPath(tmp_path):
    "with the stamp current, no product is stat'ed and nothing is pending"
    products = _mkProducts(tmp_path)
    scan, _ = _mkScan(tmp_path)
    scan.record_if_clean()
    scan2, _ = _mkScan(tmp_path)
    assert scan2.skip_scan
    assert scan2.reason == "scan stamp current"
    assert scan2.pending(products) == []          # even though no product exists
    assert scan2.all_products(products) == []
    assert not scan2.record_if_clean()             # nothing to re-record

def testNewItemForcesScan(tmp_path):
    scan, _ = _mkScan(tmp_path, items=("a", "b"))
    scan.record_if_clean()
    scan2, _ = _mkScan(tmp_path, items=("a", "b", "c"))
    assert not scan2.skip_scan
    assert scan2.reason == "item set or a watched input changed since the last scan"

def testWatchedMtimeForcesScan(tmp_path):
    watched = tmp_path / "inputs"
    watched.mkdir()
    os.utime(watched, (1000, 1000))
    scan, _ = _mkScan(tmp_path, watch=[watched])
    scan.record_if_clean()
    os.utime(watched, (2000, 2000))               # as adding a per-item subdir would
    scan2, _ = _mkScan(tmp_path, watch=[watched])
    assert not scan2.skip_scan
    assert scan2.reason == "item set or a watched input changed since the last scan"

def testLogRecordsWhichMode(tmp_path):
    msgs = []
    _mkScan(tmp_path, log=msgs.append)
    assert msgs == ["per-item scan: FULL -- no scan stamp yet"]
    scan, _ = _mkScan(tmp_path)
    scan.record_if_clean(log=msgs.append)
    _mkScan(tmp_path, log=msgs.append)
    assert msgs[1] == f"per-item scan: nothing missing, recorded {tmp_path / 'scan.stamp'}"
    assert msgs[2] == "per-item scan: SKIPPED (fast path) -- scan stamp current"

def testItemsNotReadOnFastPath(tmp_path):
    """the catalog is not even read on the fast path -- items() is called once for the
    fingerprint and never again"""
    calls = []

    def items():
        calls.append(1)
        return ("a",)

    sentinel = _touch(tmp_path / "stage.done")
    ProductScan(items=items, stamp=tmp_path / "scan.stamp",
                sentinels=[sentinel]).record_if_clean()
    del calls[:]
    scan = ProductScan(items=items, stamp=tmp_path / "scan.stamp", sentinels=[sentinel])
    scan.pending(_mkProducts(tmp_path))
    scan.all_products(_mkProducts(tmp_path))
    assert len(calls) == 1
