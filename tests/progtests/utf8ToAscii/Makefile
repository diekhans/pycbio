root = ../../..
include ${root}/defs.mk

export PYTHONPATH

utf8ToAscii = ${binDir}/utf8ToAscii

test: gdocTest

gdocTest: mkdirs
	${utf8ToAscii} input/gdoc-utf8.txt output/$@.txt
	file output/$@.txt > output/$@.type
	${diff} expected/$@.txt output/$@.txt

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
