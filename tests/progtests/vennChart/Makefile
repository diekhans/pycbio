root = ../../..
include ${root}/defs.mk

export PYTHONPATH

test: bool3PdfTest

bool3PdfTest: mkdirs
	${binDir}/vennChart input/bool3.tsv output/$@.pdf

#${diff} expected/$@.out output/$@.out

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
