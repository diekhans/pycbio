root = ../../..
include ${root}/defs.mk

export PYTHONPATH

geneCheckStats = ${binDir}/geneCheckStats

test: testAkrj

testAkrj: mkdirs
	${geneCheckStats} input/AKRJ.gene-check.tsv output/$@.stats
	${diff} expected/$@.stats output/$@.stats

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
