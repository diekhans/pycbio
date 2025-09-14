root = ../../..
include ${root}/defs.mk

spliceJunctionCheck = ${binDir}/spliceJunctionCheck

COMMON_DATA = ${root}/tests/common-output


# test data
#  grch38-regions-gencode-mod.bed modifed regions to have some bad junctions

tests: testMod

testMod: mkdirs
	${spliceJunctionCheck} --stats-tsv=output/$@.stats.tsv --nonstd-bed=output/$@.nonstd.bed ${COMMON_DATA}/grch38-regions.fa.gz input/grch38-regions-gencode-mod.bed


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
