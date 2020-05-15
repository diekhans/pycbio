root = ../../..
include ${root}/defs.mk

export PYTHONPATH

bedMappingAnalyze = ${binDir}/bedMappingAnalyze

# test data
#  - hg38.src.tm.bed, felCat9.dest.tm.bed - taken from transMap, includes some from PAR

test: testStatsTm testHistoTm

testStatsTm: mkdirs
	${bedMappingAnalyze} --report=stats --dropUniqId input/hg38.src.tm.bed input/felCat9.dest.tm.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

testHistoTm: mkdirs
	${bedMappingAnalyze} --report=histo --dropUniqId input/hg38.src.tm.bed input/felCat9.dest.tm.bed output/$@.tsv
	${diff} expected/$@.tsv output/$@.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
