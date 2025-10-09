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

test:
	@echo "to run slow running tests, use 'make slow-flow'" >&2

test-full: test-slow

test-slow: test-single test-paired-inter test-paired-split

test-single: mkdirs
	@rm -rf output/$@
	${sra_map_tool} download ${SRX2013614_TSV} output/$@
	test -e output/test-single/SRX2013614/SRR4020133.fastq.gz

test-paired-inter: mkdirs
	@rm -rf output/$@
	${sra_map_tool} download ${SRX14530460_CSV} output/$@
	test -e output/test-paired-inter/SRX14530460/SRR18396502.fastq.gz

test-paired-split: mkdirs
	@rm -rf output/$@
	${sra_map_tool} download --split-paired ${SRX14530460_CSV} output/$@
	test -e output/test-paired-split/SRX14530460/SRR18396502_1.fastq.gz
	test -e output/test-paired-split/SRX14530460/SRR18396502_2.fastq.gz


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
