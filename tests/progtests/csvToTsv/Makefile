root = ../../..
include ${root}/defs.mk

export PYTHONPATH

csvToTsv = ${runBin}/csvToTsv

test: sraRunTest

sraRunTest: mkdirs
	${csvToTsv} input/sra-run.csv output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
