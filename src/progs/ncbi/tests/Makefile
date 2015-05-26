
BIN_DIR = ../../../../bin
ncbiGbFetch = ${BIN_DIR}/ncbiGbFetch

# refseq mRNAs, ESTs
testAccver = NM_013266.2 AK289756.1 BG187649.1 U14680.1

test: gbffFetchTest faFetchTest faSimpleFetchTest

gbffFetchTest: mkdirs
	${ncbiGbFetch} --out=output/$@.gbff ${testAccver}
	diff expected/$@.gbff output/$@.gbff

faFetchTest: mkdirs
	${ncbiGbFetch} --fasta --out=output/$@.fa ${testAccver}
	diff expected/$@.fa output/$@.fa

faSimpleFetchTest: mkdirs
	${ncbiGbFetch} --fasta --simplifyIds --out=output/$@.fa ${testAccver}
	diff expected/$@.fa output/$@.fa

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
