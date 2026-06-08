# Copyright 2006-2025 Mark Diekhans
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio.hgbrowser.trackdb import (Priority, quote_setting, Track, Container,
                                      DataTrack, PslTrack, SuperTrack,
                                      CompositeTrack, TrackDb)


def testPriority():
    p = Priority()
    assert p() == 1
    assert str(p) == "1"
    p.incr()
    assert p() == 2
    p.incr(3)
    assert p() == 5
    p += 5
    assert p() == 10
    assert isinstance(p, Priority)


def testQuoteSetting():
    assert quote_setting("two words") == "two_words"
    assert quote_setting("none") == "none"


def testTrackBasic():
    trk = Track("foo", "Foo")
    assert str(trk) == ("track foo\n"
                        "shortLabel Foo\n"
                        "longLabel Foo\n"
                        "\n")


def testTrackLongLabel():
    trk = Track("foo", "Foo", "The Foo Track", color="1,2,3")
    assert str(trk) == ("track foo\n"
                        "shortLabel Foo\n"
                        "longLabel The Foo Track\n"
                        "color 1,2,3\n"
                        "\n")


def testTrackNoneDropped():
    trk = Track("foo", "Foo", color=None, html="x.html")
    assert "color" not in str(trk)
    assert "html x.html" in str(trk)


def testTrackItemAccess():
    trk = Track("foo", "Foo")
    trk["color"] = "1,2,3"
    assert trk["color"] == "1,2,3"
    trk["color"] = None          # None removes
    assert "color" not in trk.settings


def testDataTrack():
    trk = DataTrack("foo", "Foo", trackType="bigBed", bigDataUrl="foo.bb")
    s = str(trk)
    assert "type bigBed" in s
    assert "bigDataUrl foo.bb" in s
    assert "visibility hide" in s


def testPslTrackDefaults():
    trk = PslTrack("aln", "Aln", bigDataUrl="aln.bb")
    s = str(trk)
    assert "type bigPsl" in s
    assert "searchIndex name" in s
    assert "showDiffBasesMaxZoom 10000" in s


def testPslTrackOverride():
    trk = PslTrack("aln", "Aln", bigDataUrl="aln.bb",
                   visibility="full", searchIndex="name,desc")
    s = str(trk)
    assert "visibility full" in s
    assert "searchIndex name,desc" in s


def testSuperTrack():
    trk = SuperTrack("grp", "Group")
    assert "superTrack on hide" in str(trk)


def testCompositeTrack():
    trk = CompositeTrack("comp", "Comp", visibility="pack")
    s = str(trk)
    assert "compositeTrack on" in s
    assert "visibility pack" in s


def testContainerAddSetsParent():
    comp = CompositeTrack("comp", "Comp")
    sub = comp.add(DataTrack("foo", "Foo", trackType="bigBed", bigDataUrl="foo.bb"))
    assert sub.settings["parent"] == "comp"


def testContainerExplicitParentKept():
    comp = CompositeTrack("comp", "Comp")
    sub = comp.add(Track("foo", "Foo", parent="comp on"))
    assert sub.settings["parent"] == "comp on"   # setdefault leaves it


def testNestingIndentation():
    sup = SuperTrack("grp", "Group")
    comp = sup.add(CompositeTrack("comp", "Comp"))
    comp.add(PslTrack("hg38", "hg38", bigDataUrl="hg38.bb"))
    stanzas = sup.stanzas()
    assert len(stanzas) == 3
    assert stanzas[0].startswith("track grp")
    assert stanzas[1].startswith("    track comp")          # level 1
    assert stanzas[2].startswith("        track hg38")      # level 2


def testTrackDb():
    tdb = TrackDb()
    tdb.add(Track("a", "A"))
    tdb.add(Track("b", "B"))
    out = tdb.format()
    assert str(tdb) == out
    assert out.endswith("\n\n")               # last stanza also blank-terminated
    assert out.count("track ") == 2
    assert out == ("track a\nshortLabel A\nlongLabel A\n\n"
                   "track b\nshortLabel B\nlongLabel B\n\n")


def testTrackDbInitList():
    tdb = TrackDb([Track("a", "A")])
    assert "track a" in tdb.format()
