
export PYTHONPATH=../../..
binDir = ../../../bin
csvToTsv = ${binDir}/csvToTsv
diff = diff -u

test: sraRunTest

sraRunTest: mkdirs
	${csvToTsv} input/sra-run.csv output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
