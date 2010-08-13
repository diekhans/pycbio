import colorsys
from pycbio.sys.Immutable import Immutable

class Color(Immutable):
    "Color object actually representation is hidden"
    def __init__(self, r, g, b, h, s, v):
        """don't call directly use factory (from*) static methods, arguments are 0.0..1.0"""
        Immutable.__init__(self)
        self.__r = r
        self.__g = g
        self.__b = b
        self.__h = h
        self.__s = s
        self.__v = v
        self.mkImmutable()

    def __eq__(self, o):
        if o == None:
            return False
        else:
            return (self.__r == o.__r) and (self.__g == o.__g) and (self.__b == o.__b)

    def __hash__(self):
        return hash(self.__r) + hash(self.__g) + hash(self.__b)

    def __str__(self):
        return str((self.__r, self.__g, self.__b))

    @staticmethod
    def __toReal(v):
        assert(0 <= v <= 255)
        return v/255.0

    @staticmethod
    def __toInt8(v):
        iv = int(round(v*255))
        return iv

    def getRed(self):
        "get red component as a real number"
        return self.__r

    def getGreen(self):
        "get green component as a real number"
        return self.__g

    def getBlue(self):
        "get blue component as a real number"
        return self.__b

    def getHue(self):
        "get hue as a real number"
        return self.__h

    def getSaturation(self):
        "get saturation as a real number"
        return self.__s

    def getValue(self):
        "get value as a real number"
        return self.__v
    
    def getRed8(self):
        "get red component as an 8-bit int"
        return self.__toInt8(self.__r)

    def getGreen8(self):
        "get green component as an 8-bit int"
        return self.__toInt8(self.__g)

    def getBlue8(self):
        "get blue component as an 8-bit int"
        return self.__toInt8(self.__b)

    def getHue8(self):
        "get hue component as an 8-bit int"
        return self.__toInt8(self.__h)

    def getSaturation8(self):
        "get saturation component as an 8-bit int"
        return self.__toInt8(self.__s)

    def getValue8(self):
        "get value as an 8-bit number"
        return self.__toInt8(self.__v)

    def getRgb(self):
        "get RGB as tuple of real numbers"
        return (self.__r, self.__g, self.__b)

    def getRgb8(self):
        "get RGB as tuple of 8-bit ints"
        return (Color.__toInt8(self.__r), Color.__toInt8(self.__g), Color.__toInt8(self.__b))

    def getHsv(self):
        "get HSV as tuple of real numbers"
        return (self.__h, self.__s, self.__v)

    def getHsv8(self):
        "get HSV as tuple of 8-bit ints"
        return (Color.__toInt8(self.__h), Color.__toInt8(self.__s), Color.__toInt8(self.__v))

    def toHtmlColor(self):
        return "#%02x%02x%02x" % self.getRgb8()

    def toRgbStr(self, sep=",", pos=4):
        "convert to a string of real RGB values, separated by sep"
        return "%0.*f%s%0.*f%s%0.*f" % (pos, self.__r, sep, pos, self.__g, sep, pos, self.__b)

    def toRgb8Str(self, sep=","):
        "convert to a string of 8-bit RGB values, separated by sep"
        return str(Color.__toInt8(self.__r)) + sep + str(Color.__toInt8(self.__g)) + sep + str(Color.__toInt8(self.__b))

    def toHsvStr(self, sep=",", pos=4):
        "convert to a string of real HSV values, separated by sep"
        return "%0.*f%s%0.*f%s%0.*f" % (pos, self.__h, sep, pos, self.__s, sep, pos, self.__v)

    def toHsv8Str(self, sep=","):
        "convert to a string of 8-bit HSV values, separated by sep"
        return str(Color.__toInt8(self.__h)) + sep + str(Color.__toInt8(self.__s)) + sep + str(Color.__toInt8(self.__v))

    def setRed(self, red):
        "Create a new Color object with red set to the specified real number"
        return Color.fromRgb(red, self.__g, self.__b)

    def setGreen(self, green):
        "Create a new Color object with green set to the specified real number"
        return Color.fromRgb(self.__r, green, self.__b)

    def setBlue(self, blue):
        "Create a new Color object with blue set to the new real number"
        return Color.fromRgb(self.__r, self.__g, blue)

    def setHue(self, hue):
        "Create a new Color object with hue set to the specified real number"
        return Color.fromHsv(hue, self.__s, self.__v)

    def setSaturation(self, sat):
        "Create a new Color object with saturation set to the specified real number"
        return Color.fromHsv(self.__h, sat, self.__v)

    def setValue(self, val):
        "Create a new Color object with value set to the new real number"
        return Color.fromHsv(self.__h, self.__s, val)

    @staticmethod
    def fromRgb(r, g, b):
        "construct from real RGB values"
        assert((0.0 <= r <= 1.0))
        assert((0.0 <= g <= 1.0))
        assert((0.0 <= b <= 1.0))
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return Color(r, g, b, h, s, v)

    @staticmethod
    def fromRgb8(r, g, b):
        "construct from 8-bit int RGB values"
        return Color.fromRgb(Color.__toReal(r), Color.__toReal(g), Color.__toReal(b))

    @staticmethod
    def fromHsv(h, s, v):
        "construct from real HSV values"
        assert((0.0 <= h <= 1.0))
        assert((0.0 <= s <= 1.0))
        assert((0.0 <= v <= 1.0))
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return Color(r, g, b, h, s, v)
 
    @staticmethod
    def fromHsv8(h, s, v):
        "construct from 8-bit HSV values"
        return Color.fromHsv(Color.__toReal(h), Color.__toReal(s), Color.__toReal(v))

