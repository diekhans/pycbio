root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedMappingCmp = ${binDir}/bedMappingCmp

# test data
#  - set1A, set1B - hack from some transmap BED in various ways.

test: testNamePairing1 testBestNamePairing1 testNameStats1 \
	testBestOverPairing1 testOverStats1

testNamePairing1: mkdirs
	${bedMappingCmp} --report=namePairing input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testBestNamePairing1: mkdirs
	${bedMappingCmp} --report=bestNamePairing input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testNameStats1: mkdirs
	${bedMappingCmp} --report=nameStats input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testBestOverPairing1: mkdirs
	${bedMappingCmp} --report=bestOverPairing input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testOverStats1: mkdirs
	${bedMappingCmp} --report=overStats input/set1A.bed input/set1B.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
