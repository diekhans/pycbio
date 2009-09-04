
BIN_DIR = ../../../../bin

# FIXME: exonsOnlyTest currently produces no results.  Would need to implement
# a GeneFeatures object that isn't actually associated with a feature



##
# - mmRegressTest 
#   - NM_027592.1 has CDS records in weird order
# - hs_chr22.part
#   - NM_032971.1 - bad CDS record NP_116754.1

test: \
	pseudoTest geneTest pseudoIgTest geneIgTest exonsOnlyTest \
	hsRegressTest mmRegressTest rnaGeneTest \
	pseudoExtTest geneExtTest mixedRnasTest

pseudoTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --pseudo --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

geneTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

pseudoIgTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --immunoglobulins --pseudo --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

geneIgTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --immunoglobulins --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

exonsOnlyTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/exonsOnly.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

hsRegressTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/hs_regress.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

mmRegressTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --rnaq=input/mm_regress.q input/mm_regress.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

rnaGeneTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --rnaGenes --rnaq=input/hs_chrY.part.q input/hs_chrY.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

pseudoExtTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --pseudo --ext --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

geneExtTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --ext --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

# mRNA and other RNAs in same gene
mixedRnasTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --ext --rnaq=input/hs_ref_GRCh37_chrY_part.q input/hs_ref_GRCh37_chrY_part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
