
BIN_DIR = ../../../../bin

# FIXME: exonsOnlyTest currently produces no results.  Would need to implement
# a GeneFeatures object that isn't actually associated with a feature

##
# - mmRegressTest NM_027592.1 has CDS records in weird order

test: pseudoTest geneTest pseudoIgTest geneIgTest exonsOnlyTest mmRegressTest rnaGeneTest

pseudoTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --pseudo input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

geneTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

pseudoIgTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --immunoglobulins --pseudo input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

geneIgTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --immunoglobulins input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

exonsOnlyTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/exonsOnly.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

mmRegressTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/mm_chr13.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

rnaGeneTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/hs_chrY.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
