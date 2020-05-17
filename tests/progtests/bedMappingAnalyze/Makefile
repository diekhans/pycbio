root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedMappingAnalyze = ${binDir}/bedMappingAnalyze

# test data
#  - hg38.src.tm.bed, felCat9.dest.tm.bed - taken from transMap, includes some from PAR
#  - hg38 to galGal4 mappings in selected regions:
#    see ../bedMappingCmp/Makefile

galGalDir = ../bedMappingCmp/input

test: tmTests galGalTests

tmTests: testStatsTm testHistoTm

testStatsTm: mkdirs
	${bedMappingAnalyze} --report=stats --dropUniqId input/hg38.src.tm.bed input/felCat9.dest.tm.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testHistoTm: mkdirs
	${bedMappingAnalyze} --report=histo --dropUniqId input/hg38.src.tm.bed input/felCat9.dest.tm.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

galGalTests: testStatsGalGal testHistoGalGal

testStatsGalGal: mkdirs
	${bedMappingAnalyze} --report=stats --valueCol=map ${galGalDir}/hg38.src.bed ${galGalDir}/hg38-galGal4.halMap.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testHistoGalGal: mkdirs
	${bedMappingAnalyze} --report=histo --valueCol=map ${galGalDir}/hg38.src.bed ${galGalDir}/hg38-galGal4.halMap.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
