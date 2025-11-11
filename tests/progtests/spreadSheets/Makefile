root = ../../..
include ${root}/defs.mk

export PYTHONPATH

xlsx_to_tsv = ${binDir}/xlsx-to-tsv

test_xlsx = input/H9_haplotype_enriched_peaks_atac-seq.xlsx

test: xlsx-tests

xlsx-tests: testXlsxBasic

testXlsxBasic: mkdirs
	@mkdir -p output/$@
	${xlsx_to_tsv} ${test_xlsx} output/$@
	${diff} expected/$@/H9_q20_hap1_enriched_peaks.tsv output/$@/H9_q20_hap1_enriched_peaks.tsv
	${diff} expected/$@/H9_q20_hap2_enriched_peaks.tsv output/$@/H9_q20_hap2_enriched_peaks.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
