
BIN_DIR = ../../../../bin

test: pseudoTest geneTest pseudoIgTest geneIgTest exonsOnlyTest


pseudoTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --pseudogenes input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

geneTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred input/hs_chr22.part.gbs output/$@.gp
	genePredCheck output/$@.gp
	diff expected/$@.gp output/$@.gp

pseudoIgTest: mkdirs
	${BIN_DIR}/gbffGenesToGenePred --pseudoimmunos input/hs_chr22.part.gbs output/$@.gp
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


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
