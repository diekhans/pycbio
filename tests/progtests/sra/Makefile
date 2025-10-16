root = ../../..
include ${root}/defs.mk

##
# test cases
#
#  SRX14530460/SRR18396502
#     Saccharomyces cerevisiae
#     RNA-Seq PAIRED
#     76kb fastq
#
#  SRX2013614/SRR4020133
#     Saccharomyces cerevisiae
#     RNA-Seq SINGLE
#     101kb fastq
##

SRX14530460_CSV = input/SRX14530460-SraRunInfo.csv
SRX2013614_TSV  = input/SRX2013614-SraRunInfo.tsv

sra_map_tool = ${binDir}/sra-map-tool

test: test-fast
	@echo "to run slow running tests, use 'make slow-flow' or 'make test-full'" >&2

test-full: test-fast test-slow

test-fast: test-jobs-single test-jobs-paired-inter test-jobs-paired-split
test-slow: test-down-single test-down-paired-inter test-down-paired-split

test-down-single: mkdirs
	@rm -rf output/$@
	${sra_map_tool} download ${SRX2013614_TSV} output/$@
	test -e output/test-down-single/SRX2013614/SRR4020133.fastq.gz

test-down-paired-inter: mkdirs
	@rm -rf output/$@
	${sra_map_tool} download ${SRX14530460_CSV} output/$@
	test -e output/test-down-paired-inter/SRX14530460/SRR18396502.fastq.gz

test-down-paired-split: mkdirs
	@rm -rf output/$@
	${sra_map_tool} download --split-paired ${SRX14530460_CSV} output/$@
	test -e output/test-down-paired-split/SRX14530460/SRR18396502_1.fastq.gz
	test -e output/test-down-paired-split/SRX14530460/SRR18396502_2.fastq.gz

test-jobs-single: mkdirs
	@rm -rf output/$@
	${sra_map_tool} align-jobs ${SRX2013614_TSV} output/$@/fastqs output/$@/aligns output/$@.jobs mapper fred
	diff expected/$@.jobs output/$@.jobs

test-jobs-paired-inter: mkdirs
	@rm -rf output/$@
	${sra_map_tool} align-jobs ${SRX14530460_CSV} output/$@/fastqs output/$@/aligns output/$@.jobs -- mapper barney
	diff expected/$@.jobs output/$@.jobs

test-jobs-paired-split: mkdirs
	@rm -rf output/$@
	${sra_map_tool} align-jobs --split-paired ${SRX14530460_CSV} output/$@/fastqs output/$@/aligns output/$@.jobs mapper wilma
	diff expected/$@.jobs output/$@.jobs

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
