# Copyright 2006-2025 Mark Diekhans
"""
Create trackDb files for hubs.
"""

INDENT = "    "


class Priority:
    "auto-incrementing priority counter for ordering tracks"
    def __init__(self, val=1):
        self.val = val

    def __call__(self):
        return self.val

    def __str__(self):
        return str(self.val)

    def incr(self, val=1):
        self.val += val

    def __iadd__(self, val):
        self.val += val
        return self


def quote_setting(v):
    "replace spaces so a value can be used in a space-delimited context"
    return v.replace(' ', '_')


class Track:
    """A trackDb track stanza.  Settings come from the class DEFAULTS, the
    settings dict (for names that aren't valid keywords, e.g. dotted names),
    and keyword arguments, merged in that order so later sources win.  Settings
    with a value of None are dropped."""

    DEFAULTS = {}

    def __init__(self, track, shortLabel, *, longLabel=None, settings=None, **kwargs):
        self.track = track
        self.shortLabel = shortLabel
        self.longLabel = longLabel if longLabel is not None else shortLabel
        merged = self.DEFAULTS | (settings or {}) | kwargs
        self.settings = {k: v for k, v in merged.items() if v is not None}

    def __setitem__(self, key, val):
        if val is None:
            self.settings.pop(key, None)
        else:
            self.settings[key] = val

    def __getitem__(self, key):
        return self.settings[key]

    def _own_lines(self):
        lines = [
            f"track {self.track}",
            f"shortLabel {self.shortLabel}",
            f"longLabel {self.longLabel}",
        ]
        for key, val in self.settings.items():
            lines.append(f"{key} {val}")
        return lines

    def stanzas(self, level=0):
        """Return this track (and any subtracks) as a list of stanza strings,
        each indented for the given nesting level."""
        prefix = INDENT * level
        return ['\n'.join(prefix + line for line in self._own_lines())]

    def __str__(self):
        return ''.join(stanza + '\n\n' for stanza in self.stanzas())


class Container(Track):
    """A track that contains subtracks (e.g. super or composite track)."""

    def __init__(self, track, shortLabel, *, longLabel=None, settings=None, **kwargs):
        super().__init__(track, shortLabel, longLabel=longLabel, settings=settings, **kwargs)
        self.subtracks = []

    def add(self, subtrack):
        "add a subtrack, defaulting its parent to this container; returns it"
        subtrack.settings.setdefault("parent", self.track)
        self.subtracks.append(subtrack)
        return subtrack

    def stanzas(self, level=0):
        stanzas = super().stanzas(level)
        for subtrack in self.subtracks:
            stanzas.extend(subtrack.stanzas(level + 1))
        return stanzas


class DataTrack(Track):
    "a track displaying data from a bigDataUrl"

    DEFAULTS = {
        "visibility": "hide",
    }

    def __init__(self, track, shortLabel, *, longLabel=None,
                 trackType, bigDataUrl, settings=None, **kwargs):
        super().__init__(track, shortLabel, longLabel=longLabel, settings=settings,
                         type=trackType, bigDataUrl=bigDataUrl, **kwargs)


class PslTrack(DataTrack):
    "a bigPsl alignment track with the usual indel/diff-base settings"

    DEFAULTS = {
        **DataTrack.DEFAULTS,
        "searchIndex": "name",
        "baseColorUseSequence": "lfExtra",
        "indelDoubleInsert": "on",
        "indelQueryInsert": "on",
        "showDiffBasesAllScales": ".",
        "showDiffBasesMaxZoom": 10000,
    }

    def __init__(self, track, shortLabel, *, longLabel=None,
                 bigDataUrl, settings=None, **kwargs):
        super().__init__(track, shortLabel, longLabel=longLabel, settings=settings,
                         trackType="bigPsl", bigDataUrl=bigDataUrl, **kwargs)


class SuperTrack(Container):
    "a super track grouping other tracks"

    DEFAULTS = {
        "superTrack": "on hide",
    }


class CompositeTrack(Container):
    "a composite track grouping subtracks"

    DEFAULTS = {
        "compositeTrack": "on",
        "visibility": "hide",
    }


class TrackDb:
    "collection of top-level tracks making up a trackDb file"

    def __init__(self, tracks=()):
        self.tracks = list(tracks)

    def add(self, track):
        "add a top-level track; returns it"
        self.tracks.append(track)
        return track

    def format(self):
        "format all tracks into a complete trackDb string"
        stanzas = []
        for track in self.tracks:
            stanzas.extend(track.stanzas())
        return ''.join(stanza + '\n\n' for stanza in stanzas)

    def __str__(self):
        return self.format()
