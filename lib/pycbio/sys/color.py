# Copyright 2006-2012 Mark Diekhans
import re
import colorsys
from collections import namedtuple

# FIXME: add optional alpha.
# FIXME: do we really need to store both RGB and HSV?


class Color(namedtuple("Color", ("red", "green", "blue",
                                 "hue", "saturation", "value"))):
    """Immutable color object with conversion to/from different formats.
    Don't construct  directly use, factory (from*) static methods.

    :ivar red: red channel, in the range 0.0..1.0
    :ivar green: green channel, in the range 0.0..1.0
    :ivar blue: blue channel, in the range 0.0..1.0
    :ivar hue: hue component, in the range 0.0..1.0
    :ivar saturation: saturation component in the range 0.0..1.0
    :ivar value: value component, in the range 0.0..1.0
    """
    __slots__ = ()

    def __str__(self):
        return str((self.red, self.green, self.blue))

    @staticmethod
    def _int8ToReal(v):
        assert 0 <= v <= 255
        return v / 255.0

    @staticmethod
    def _realToInt8(v):
        return int(round(v * 255))

    @property
    def red8(self):
        "red channel as an 8-bit int"
        return self._realToInt8(self.red)

    @property
    def green8(self):
        "green channel as an 8-bit int"
        return self._realToInt8(self.green)

    @property
    def blue8(self):
        "get blue channel as an 8-bit int"
        return self._realToInt8(self.blue)

    @property
    def huei(self):
        "hue component as an integer angle"
        return int(round(360 * self.hue))

    @property
    def saturationi(self):
        "saturation component as an integer percent"
        return int(round(100 * self.saturation))

    @property
    def valuei(self):
        "value component as an integer percent"
        return int(round(100 * self.value))

    @property
    def rgb(self):
        "RGB as tuple of real numbers"
        return (self.red, self.green, self.blue)

    @property
    def rgb8(self):
        "RGB as tuple of 8-bit ints"
        return (self._realToInt8(self.red), self._realToInt8(self.green), self._realToInt8(self.blue))

    @property
    def packRgb8(self):
        "return packed 8-bit int RGB values (e.g.#008000)"
        return (self._realToInt8(self.red) << 16) | (self._realToInt8(self.green) << 8) | self._realToInt8(self.blue)

    @property
    def hsv(self):
        "HSV as tuple of real numbers"
        return (self.hue, self.saturation, self.value)

    @property
    def hsvi(self):
        "HSV as tuple of integers"
        return (self.huei, self.saturationi, self.valuei)

    def toHtmlColor(self):
        "as an html color"
        return "#%02x%02x%02x" % self.rgb8

    def toRgbStr(self, sep=",", pos=4):
        "convert to a string of real RGB values, separated by sep"
        return "%0.*f%s%0.*f%s%0.*f" % (pos, self.red, sep, pos, self.green, sep, pos, self.blue)

    def toRgb8Str(self, sep=","):
        "convert to a string of 8-bit RGB values, separated by sep"
        return "{}{}{}{}{}".format(self._realToInt8(self.red), sep, self._realToInt8(self.green), sep, self._realToInt8(self.blue))

    def toHsvStr(self, sep=",", pos=4):
        "convert to a string of real HSV values, separated by sep"
        return "%0.*f%s%0.*f%s%0.*f" % (pos, self.hue, sep, pos, self.saturation, sep, pos, self.value)

    def toHsviStr(self, sep=","):
        "convert to a string of integer HSV values, separated by sep"
        return "{}{}{}{}{}".format(self.huei, sep, self.saturationi, sep, self.valuei)

    def setRed(self, red):
        "Create a new Color object with red set to the specified real number"
        return self.fromRgb(red, self.green, self.blue)

    def setGreen(self, green):
        "Create a new Color object with green set to the specified real number"
        return self.fromRgb(self.red, green, self.blue)

    def setBlue(self, blue):
        "Create a new Color object with blue set to the new real number"
        return self.fromRgb(self.red, self.green, blue)

    def setHue(self, hue):
        "Create a new Color object with hue set to the specified real number"
        return self.fromHsv(hue, self.saturation, self.value)

    def setSaturation(self, sat):
        "Create a new Color object with saturation set to the specified real number"
        return self.fromHsv(self.hue, sat, self.value)

    def setValue(self, val):
        "Create a new Color object with value set to the new real number"
        return self.fromHsv(self.hue, self.saturation, val)

    @staticmethod
    def fromRgb(r, g, b):
        "construct from real RGB values"
        assert (0.0 <= r <= 1.0)
        assert (0.0 <= g <= 1.0)
        assert (0.0 <= b <= 1.0)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return Color(r, g, b, h, s, v)

    @staticmethod
    def fromRgb8(r, g, b):
        "construct from 8-bit int RGB values"
        return Color.fromRgb(Color._int8ToReal(r), Color._int8ToReal(g), Color._int8ToReal(b))

    @staticmethod
    def fromPackRgb8(c):
        "construct from packed 8-bit int RGB values (e.g.#008000)"
        r = (c >> 16) & 0xff
        g = (c >> 8) & 0xff
        b = c & 0xff
        return Color.fromRgb(Color._int8ToReal(r), Color._int8ToReal(g), Color._int8ToReal(b))

    @staticmethod
    def fromHsv(h, s, v):
        "construct from real HSV values"
        assert (0.0 <= h <= 1.0)
        assert (0.0 <= s <= 1.0)
        assert (0.0 <= v <= 1.0)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return Color(r, g, b, h, s, v)

    @staticmethod
    def fromHsvi(h, s, v):
        "construct from integer HSV values"
        return Color.fromHsv(h / 306.0, s / 100.0, v / 100.0)

    @staticmethod
    def fromHtmlColor(hcolor):
        "construct from a HTML color string in the form #804c66"
        mat = re.match("^#([0-9a-fA-F]{6})$", hcolor)
        if not mat:
            raise ValueError("invalid HTML color: {}".format(hcolor))
        return Color.fromPackRgb8(int(mat.group(1), base=16))
