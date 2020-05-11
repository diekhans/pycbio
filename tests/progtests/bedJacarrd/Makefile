root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedJaccard = ${binDir}/bedJaccard

# test data
#  - set1A, set1B - hack from some transmap BED in various ways.

test: testPairings1 testBestPairings1 testStats1

testPairings1: mkdirs
	${bedJaccard} --report=pairings input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testBestPairings1: mkdirs
	${bedJaccard} --report=bestPairings input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testStats1: mkdirs
	${bedJaccard} --report=stats input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
