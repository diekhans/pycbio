root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedToCdsBed = ${binDir}/bedToCdsBed

# test data
#  - hg38 to galGal4 mappings in selected regions:
#    see ../bedMappingCmp/Makefile (now in branch)

galGalDir = ./input

test: targetBedTest mappedBedTest

targetBedTest: mkdirs
	${bedToCdsBed} ${galGalDir}/galGal4.target.bed output/$@.bed
	diff expected/$@.bed output/$@.bed

mappedBedTest: mkdirs
	${bedToCdsBed} ${galGalDir}/hg38-galGal4.halMap.bed output/$@.bed
	diff expected/$@.bed output/$@.bed


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
