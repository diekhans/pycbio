root = ../../..
include ${root}/defs.mk

export PYTHONPATH

csvToTsv = ${binDir}/csv-to-tsv

test: sraRunTest sraRunDerivedTest sraRunDelimTest

sraRunTest: mkdirs
	${csvToTsv} input/sra-run.csv output/$@.tsv
	${diff} expected/sraRunTest.tsv output/$@.tsv

sraRunDerivedTest: mkdirs
	cp input/sra-run.csv output/$@.csv
	${csvToTsv} output/$@.csv
	${diff} expected/sraRunTest.tsv output/$@.tsv

sraRunDelimTest: mkdirs
	${csvToTsv} --delimiter=';' input/sra-run-semi.csv output/$@.tsv
	${diff} expected/sraRunTest.tsv output/$@.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output