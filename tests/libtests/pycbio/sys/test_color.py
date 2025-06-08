# Copyright 2006-2025 Mark Diekhans
import sys
import pickle
import pytest
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")
from pycbio import PycbioException
from pycbio.sys.color import Color
from pycbio.sys.svgcolors import SvgColors


def _assertRgb(color, r, g, b, a=None):
    assert color.red == pytest.approx(r)
    assert color.green == pytest.approx(g)
    assert color.blue == pytest.approx(b)
    assert color.alpha == pytest.approx(a)

def _assertHsv(color, h, s, v, a=None):
    assert color.hue == pytest.approx(h)
    assert color.saturation == pytest.approx(s)
    assert color.value == pytest.approx(v)
    assert color.alpha == pytest.approx(a)

def testRealRgb():
    c = Color.fromRgb(0.5, 0.3, 0.4)
    _assertRgb(c, 0.5, 0.3, 0.4)
    _assertRgb(c.setRed(0), 0.0, 0.3, 0.4)
    _assertRgb(c.setGreen(1.0), 0.5, 1.0, 0.4)
    _assertRgb(c.setBlue(0.2), 0.5, 0.3, 0.2)
    rgb = c.rgb
    assert rgb[0] == pytest.approx(0.5)
    assert rgb[1] == pytest.approx(0.3)
    assert rgb[2] == pytest.approx(0.4)
    assert c.rgb8 == (128, 76, 102)
    _assertHsv(c, 0.9166666666, 0.4, 0.5)
    _assertHsv(c.setHue(0.2), 0.2, 0.4, 0.5)
    _assertHsv(c.setSaturation(0.2), 0.9166666666, 0.2, 0.5)
    _assertHsv(c.setValue(1.0), 0.9166666666, 0.4, 1.0)
    hsv = c.hsv
    assert hsv[0] == pytest.approx(0.9166666666)
    assert hsv[1] == pytest.approx(0.4)
    assert hsv[2] == pytest.approx(0.5)
    assert c.hsv8 == (330, 40, 50)
    assert c.toHtmlColor() == "#804c66"

def testRealRgba():
    c = Color.fromRgb(0.5, 0.3, 0.4, 0.9)
    _assertRgb(c, 0.5, 0.3, 0.4, 0.9)
    _assertRgb(c.setRed(0), 0.0, 0.3, 0.4, 0.9)
    _assertRgb(c.setGreen(1.0), 0.5, 1.0, 0.4, 0.9)
    _assertRgb(c.setBlue(0.2), 0.5, 0.3, 0.2, 0.9)
    _assertRgb(c.setAlpha(0.7), 0.5, 0.3, 0.4, 0.7)
    rgba = c.rgba
    assert rgba[0] == pytest.approx(0.5)
    assert rgba[1] == pytest.approx(0.3)
    assert rgba[2] == pytest.approx(0.4)
    assert rgba[3] == pytest.approx(0.9)
    assert c.rgba8, (128, 76, 102, 230)
    _assertHsv(c, 0.9166666666, 0.4, 0.5, 0.9)
    _assertHsv(c.setHue(0.2), 0.2, 0.4, 0.5, 0.9)
    _assertHsv(c.setSaturation(0.2), 0.9166666666, 0.2, 0.5, 0.9)
    _assertHsv(c.setValue(1.0), 0.9166666666, 0.4, 1.0, 0.9)
    hsva = c.hsva
    assert hsva[0] == pytest.approx(0.9166666666)
    assert hsva[1] == pytest.approx(0.4)
    assert hsva[2] == pytest.approx(0.5)
    assert hsva[3] == pytest.approx(0.9)
    assert c.hsva8, (330, 40, 50, 230)

def testHtmlColor():
    c = Color.fromHtmlColor("#804c66")
    assert c.toHtmlColor() == "#804c66"

def testRgb8Str():
    assert Color.fromRgb8Str("255,182,3") == Color.fromRgb8(255, 182, 3)
    with pytest.raises(ValueError, match="invalid RGB8 color string: 255,182"):
        Color.fromRgb8Str("255,182")
    with pytest.raises(ValueError, match="invalid RGB8 color string: 255,182"):
        Color.fromRgb8Str("255,182,399")

def testPackRgb8():
    assert Color.fromPackRgb8(0x008000) == Color.fromRgb8(0x00, 0x80, 0x00)
    assert Color.fromPackRgb8(0xFFA510) == Color.fromRgb8(0xFF, 0xA5, 0x10)
    assert Color.fromPackRgb8(0x008000).packRgb8 == 0x008000
    assert Color.fromPackRgb8(0xFFA510).packRgb8 == 0xFFA510

def testRegress():
    c = Color.fromRgb8(16, 78, 139)
    assert c.red8 == 16
    assert c.green8 == 78
    assert c.blue8 == 139
    assert c.toRgb8Str() == "16,78,139"
    assert c.toHsv8Str() == "210,88,55"
    assert c.toHtmlColor() == "#104e8b"

def testImmutable():
    c = Color.fromRgb8(16, 78, 139)
    with pytest.raises(AttributeError):
        c.red = 0

def testDistance():
    c1 = Color.fromRgb(0.5, 0.3, 0.4)
    c2 = Color.fromRgb(0.9, 0.5, 0.1)
    assert c1.distance(c1) == 0.0
    assert c1.distance(c2) == pytest.approx(0.5385164807)

def testAliceBlue():
    assert SvgColors.aliceblue == Color.fromRgb8(0xf0, 0xf8, 0xff)

def testBlack():
    assert SvgColors.black == Color.fromRgb(0.0, 0.0, 0.0)

def testLookup():
    assert SvgColors.yellowgreen == SvgColors.lookup("yellowgreen")

def testLoopupErr():
    with pytest.raises(PycbioException, match="^unknown SVG color 'fred'$"):
        SvgColors.lookup("fred")

def testLookupBad():
    with pytest.raises(PycbioException, match="^unknown SVG color 'evil'$"):
        SvgColors.lookup("evil")

def testGetColors():
    assert "whitesmoke" in SvgColors.getNames()
    assert "skyblue" in SvgColors.getNames()

def testClosest():
    assert SvgColors.getClosestName(SvgColors.skyblue) == "skyblue"
    assert SvgColors.getClosestColor(SvgColors.skyblue) == SvgColors.skyblue

    # skyblue is 0x87ceeb
    near = Color.fromPackRgb8(0x87ceed)
    assert SvgColors.getClosestName(near) == "skyblue"
    assert SvgColors.getClosestColor(near) == SvgColors.skyblue

def testGetName():
    assert SvgColors.getName(SvgColors.skyblue) == "skyblue"

def testGetNameObjErr():
    with pytest.raises(PycbioException, match="^object is not a Color '<class 'dict'>'$"):
        SvgColors.getName(dict())

def testGetNameNotSvgErr():
    with pytest.raises(PycbioException, match="^color is not an SVG color object '0.1200,0.4500,0.0010'$"):
        SvgColors.getName(Color.fromRgb(0.12, 0.45, 0.001))

def testComplementary():
    c1 = Color.fromRgb(0.5, 0.3, 0.4)
    assert c1.complementary() == Color.fromRgb(0.5, 0.7, 0.6)

def testPickle():
    c1 = Color.fromRgb(0.5, 0.3, 0.4)
    c1pkl = pickle.dumps(c1)
    c2 = pickle.loads(c1pkl)
    assert c1, c2
