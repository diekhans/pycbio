root = ../../..
include ${root}/defs.mk

export PYTHONPATH

gbffGenesToGenePred = ${binDir}/gbffGenesToGenePred

# FIXME: exonsOnlyTest currently produces no results.  Would need to implement
# a GeneFeatures object that isn't actually associated with a feature


##
# - mmRegressTest
#   - NM_027592.1 has CDS records in weird order
# - hs_chr22.part
#   - NM_032971.1 - bad CDS record NP_116754.1

test: \
	pseudoTest geneTest dropLocusVerTest pseudoIgTest geneIgTest exonsOnlyTest \
	hsRegressTest mmRegressTest rnaGeneTest rnaGeneTabMapTest pseudoExtTest geneExtTest \
	mixedRnasTest ribShiftTest allGenesTest refSeqTest

pseudoTest: mkdirs
	${gbffGenesToGenePred} --pseudo --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

geneTest: mkdirs
	${gbffGenesToGenePred} --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

dropLocusVerTest: mkdirs
	${gbffGenesToGenePred} --dropLocusVer --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

pseudoIgTest: mkdirs
	${gbffGenesToGenePred} --immunoglobulins --pseudo --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

geneIgTest: mkdirs
	${gbffGenesToGenePred} --immunoglobulins --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp  >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

exonsOnlyTest: mkdirs
	${gbffGenesToGenePred} --ignoreShortSequence input/exonsOnly.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

hsRegressTest: mkdirs
	${gbffGenesToGenePred} input/hs_regress.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

mmRegressTest: mkdirs
	${gbffGenesToGenePred} --rnaq=input/mm_regress.q input/mm_regress.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

rnaGeneTest: mkdirs
	${gbffGenesToGenePred} --rnaGenes --rnaq=input/hs_chrY.part.q input/hs_chrY.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

rnaGeneTabMapTest: mkdirs
	${gbffGenesToGenePred} --rnaGenes --mrnaProtMap=input/hs_chrY.part.mrna2prot input/hs_chrY.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

pseudoExtTest: mkdirs
	${gbffGenesToGenePred} --pseudo --ext --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

geneExtTest: mkdirs
	${gbffGenesToGenePred} --ext --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

# mRNA and other RNAs in same gene
mixedRnasTest: mkdirs
	${gbffGenesToGenePred} --ext --rnaq=input/hs_ref_GRCh37_chrY_part.q input/hs_ref_GRCh37_chrY_part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

# ribosomal frame shift
ribShiftTest: mkdirs
	${gbffGenesToGenePred} --errorOnWarn --ext input/mmu_ribFrameShift.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

allGenesTest: mkdirs
	${gbffGenesToGenePred} --allGenes --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out

refSeqTest: mkdirs
	${gbffGenesToGenePred} --allGenes --refSeqOnly --rnaq=input/hs_chr22.part.q input/hs_chr22.part.gbs output/$@.gp >output/$@.out 2>&1
	genePredCheck output/$@.gp
	${diff} expected/$@.gp output/$@.gp
	${diff} expected/$@.out output/$@.out


mkdirs:
	@mkdir -p output

clean:
	rm -rf output
