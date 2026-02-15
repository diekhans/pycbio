root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedToCdsBed = ${binDir}/bedToCdsBed
bedToIntronBed = ${binDir}/bedToIntronBed

# test data
#  - hg38 to galGal4 mappings in selected regions:
#  - hg38 bed of some GENCODE annotations

galGalDir = ./input

test:  bedToCdsBedTests bedToIntronBedTests

###
bedToCdsBedTests: targetCdsBedTest mappedCdsBedTest 

targetCdsBedTest: mkdirs
	${bedToCdsBed} input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

mappedCdsBedTest: mkdirs
	${bedToCdsBed} input/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

###
bedToIntronBedTests:  bedIntronTest bedIntronMinIntronTest bedIntronUniqueNameTest bedIntronUniqueTest \
	bedIntronBaseBoundsTest bedIntronExonBoundsTest bedIntronMinIntronGapTest

bedIntronTest: mkdirs
	${bedToIntronBed} input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

# lots of gaps in mapped (default is--minIntronSize=30)
bedIntronMinIntronTest: mkdirs
	${bedToIntronBed} input/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronMinIntronGapTest: mkdirs
	${bedToIntronBed} --minIntronSize=0 input/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronUniqueNameTest: mkdirs
	${bedToIntronBed} --uniqueName input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronUniqueTest: mkdirs
	${bedToIntronBed} --unique input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronBaseBoundsTest: mkdirs
	${bedToIntronBed} --fmt=base-bounds input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronExonBoundsTest: mkdirs
	${bedToIntronBed} --fmt=exon-bounds input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed



mkdirs:
	@mkdir -p output

clean:
	rm -rf output
