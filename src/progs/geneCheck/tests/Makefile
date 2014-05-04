
binDir = ../../../../bin

test: testAkrj

testAkrj: mkdirs
	${binDir}/geneCheckStats input/AKRJ.gene-check.tsv output/$@.stats
	diff expected/$@.stats output/$@.stats

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
