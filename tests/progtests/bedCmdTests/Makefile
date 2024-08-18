root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedToCdsBed = ${binDir}/bedToCdsBed
bedToIntronBed = ${binDir}/bedToIntronBed

# test data
#  - hg38 to galGal4 mappings in selected regions:
#  - hg38 bed of some GENCODE annotations

galGalDir = ./input

test:   targetBedTest mappedBedTest mappedBedTest \
	bedIntronMinIntronTest bedIntronNoUniqTest bedIntronNoUniqTest

targetBedTest: mkdirs
	${bedToCdsBed} input/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

mappedBedTest: mkdirs
	${bedToCdsBed} input/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronMinIntronTest: mkdirs
	${bedToIntronBed} --minIntronSize=30 input/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

bedIntronNoUniqTest: mkdirs
	${bedToIntronBed} --noUniqSuffix input/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
