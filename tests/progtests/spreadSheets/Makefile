root = ../../..
include ${root}/defs.mk

export PYTHONPATH

xlsx_to_tsv = ${binDir}/xlsx-to-tsv
tsv_to_xlsx = ${binDir}/tsv-to-xlsx

test_xlsx = input/H9_haplotype_enriched_peaks_atac-seq.xlsx

test: xlsx-tests tsv-tests

xlsx-tests: testXlsxBasic

testXlsxBasic: mkdirs
	@mkdir -p output/$@
	${xlsx_to_tsv} ${test_xlsx} output/$@
	${diff} expected/$@/H9_q20_hap1_enriched_peaks.tsv output/$@/H9_q20_hap1_enriched_peaks.tsv
	${diff} expected/$@/H9_q20_hap2_enriched_peaks.tsv output/$@/H9_q20_hap2_enriched_peaks.tsv

tsv-tests: testTsvToXlsxRoundTrip

# build a multi-sheet workbook from TSVs, convert it back, and confirm the
# round-trip reproduces the inputs (xlsx is binary, so we diff the TSVs)
testTsvToXlsxRoundTrip: mkdirs
	@mkdir -p output/$@
	${tsv_to_xlsx} output/$@/combined.xlsx input/genes.tsv input/samples.tsv
	${xlsx_to_tsv} output/$@/combined.xlsx output/$@
	${diff} input/genes.tsv output/$@/genes.tsv
	${diff} input/samples.tsv output/$@/samples.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
