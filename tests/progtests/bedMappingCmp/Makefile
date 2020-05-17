root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedMappingCmp = ${binDir}/bedMappingCmp

# test data
#  - set1A, set1B - hack from some transmap BED in various ways.
#  - hg38 to galGal4 mappings in selected regions:
#     - hg38.src.bed - source transcripts that were mapped
#     - hg38-galGal4.halMap.bed - hg38 to galGal4 using HAL alignments
#     - hg38-galGal4.lastzMap.bed - hg38 to galGal4 using LASTZ alignments
#     - galGal4.target.bed - Ensembl annotations in regions

test: set1Tests galGalTests


set1Tests: testNamePairing1 testBestNamePairing1 testNameStats1 \
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


galGalTests: testNamePairingGalGal testBestNamePairingGalGal testNameStatsGalGal \
	testBestOverPairingGalGal testOverStatsGalGal

testNamePairingGalGal: mkdirs
	${bedMappingCmp} --report=namePairing input/hg38-galGal4.lastzMap.bed input/hg38-galGal4.halMap.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testBestNamePairingGalGal: mkdirs
	${bedMappingCmp} --report=bestNamePairing --floatPrecision=2 input/hg38-galGal4.lastzMap.bed input/hg38-galGal4.halMap.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testNameStatsGalGal: mkdirs
	${bedMappingCmp} --report=nameStats --floatPrecision=2 input/hg38-galGal4.lastzMap.bed input/hg38-galGal4.halMap.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testBestOverPairingGalGal: mkdirs
	${bedMappingCmp} --report=bestOverPairing input/hg38-galGal4.lastzMap.bed input/galGal4.target.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testOverStatsGalGal: mkdirs
	${bedMappingCmp} --report=overStats input/hg38-galGal4.lastzMap.bed input/galGal4.target.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv



mkdirs:
	@mkdir -p output

clean:
	rm -rf output
