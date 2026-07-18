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

tsv-tests: testTsvToXlsxRoundTrip testTsvToXlsxHeaderXform testTsvToXlsxPairs testTsvToXlsxSheetNameSubst

# build a multi-sheet workbook from TSVs, convert it back, and confirm the
# round-trip reproduces the inputs (xlsx is binary, so we diff the TSVs)
testTsvToXlsxRoundTrip: mkdirs
	@mkdir -p output/$@
	${tsv_to_xlsx} output/$@/combined.xlsx input/genes.tsv input/samples.tsv
	${xlsx_to_tsv} output/$@/combined.xlsx output/$@
	${diff} input/genes.tsv output/$@/genes.tsv
	${diff} input/samples.tsv output/$@/samples.tsv

# a regex header substitution plus the default identifier conversion rewrites
# the column headers; convert back and diff to confirm the transformed headers
testTsvToXlsxHeaderXform: mkdirs
	@mkdir -p output/$@
	${tsv_to_xlsx} --header-subst '^Gene ID$$' gene output/$@/measurements.xlsx input/measurements.tsv
	${xlsx_to_tsv} output/$@/measurements.xlsx output/$@
	${diff} expected/$@/measurements.tsv output/$@/measurements.tsv

# --pairs takes alternating SHEET_NAME TSV arguments; check the sheet names
# drive the output file names on the way back
testTsvToXlsxPairs: mkdirs
	@mkdir -p output/$@
	${tsv_to_xlsx} --pairs output/$@/combined.xlsx Genes input/genes.tsv Samples input/samples.tsv
	${xlsx_to_tsv} output/$@/combined.xlsx output/$@
	${diff} expected/$@/Genes.tsv output/$@/Genes.tsv
	${diff} expected/$@/Samples.tsv output/$@/Samples.tsv

# --sheet-name-subst rewrites the sheet names derived from the input file names
# (here stripping a common prefix); the substituted names drive the output file
# names on the way back
testTsvToXlsxSheetNameSubst: mkdirs
	@mkdir -p output/$@
	${tsv_to_xlsx} --sheet-name-subst '^dataset_v1\.' '' output/$@/combined.xlsx input/dataset_v1.genes.tsv input/dataset_v1.samples.tsv
	${xlsx_to_tsv} output/$@/combined.xlsx output/$@
	${diff} input/genes.tsv output/$@/genes.tsv
	${diff} input/samples.tsv output/$@/samples.tsv

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
