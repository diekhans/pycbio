root = ../../..
include ${root}/defs.mk

export PYTHONPATH

ncbiGbFetch = ${binDir}/ncbiGbFetch
ncbiAssemblyReportConvert = ${binDir}/ncbiAssemblyReportConvert
agpToPsl = ${binDir}/agpToPsl

ncbiTestInputDir = ../../libtests/pycbio/ncbi/input

# refseq mRNAs, ESTs
testAccver = NM_013266.3 AK289756.1 BG187649.1 U14680.1

diff = diff -u

# if there is no domain configured, we need to for an email address for ncbiGbFetch
ifeq ($(findstring .,$(shell hostname -f)),)
   email = --email=markd@ucsc.edu
endif


test: fetchTests asmReportCnvTests agpToPslTests

fetchTests: \
	gbffFetchTest faFetchTest

gbffFetchTest: mkdirs
	${ncbiGbFetch} ${email} --out=output/$@.gbff ${testAccver}
	${diff} expected/$@.gbff output/$@.gbff

faFetchTest: mkdirs
	${ncbiGbFetch} ${email} --fasta --out=output/$@.fa ${testAccver}
	${diff} expected/$@.fa output/$@.fa

asmReportCnvTests: \
	asmSeqNameUcscLiftTest asmRefSeqGencodeLiftTest \
	asmSeqNameUcscPslTest asmRefSeqGencodePslTest \
	asmSeqNameSizesTest asmGencodeNameSizesMainChromsTest asmGencodeNameSizesMainAsmTest \
	asmIdmapTest asmIdmapMainAsmTest asmIdmapMixedAsmTest asmUmappedErrTest \

asmReportTestFile = ${ncbiTestInputDir}/GCF_000001405.28.assembly.txt

asmSeqNameUcscLiftTest: mkdirs
	${ncbiAssemblyReportConvert} --skipUnmapped --fromIdType=sequenceName --toIdType=ucscStyleName lift ${asmReportTestFile} output/$@.lift 2>output/$@.err
	${diff} expected/$@.lift output/$@.lift
	${diff} expected/$@.err output/$@.err

asmRefSeqGencodeLiftTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=refSeqAccn --toIdType=gencode lift ${asmReportTestFile} output/$@.lift
	${diff} expected/$@.lift output/$@.lift

asmSeqNameUcscPslTest: mkdirs
	${ncbiAssemblyReportConvert} --skipUnmapped --fromIdType=sequenceName --toIdType=ucscStyleName psl ${asmReportTestFile} output/$@.psl 2>output/$@.err
	pslCheck -verbose=0 output/$@.psl
	${diff} expected/$@.psl output/$@.psl
	${diff} expected/$@.err output/$@.err

asmRefSeqGencodePslTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=refSeqAccn --toIdType=gencode psl ${asmReportTestFile} output/$@.psl
	pslCheck -verbose=0 output/$@.psl
	${diff} expected/$@.psl output/$@.psl

asmSeqNameSizesTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=sequenceName sizes ${asmReportTestFile} output/$@.sizes
	${diff} expected/$@.sizes output/$@.sizes

asmGencodeNameSizesMainChromsTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=gencode --include=mainChroms sizes ${asmReportTestFile} output/$@.sizes
	${diff} expected/$@.sizes output/$@.sizes

asmGencodeNameSizesMainAsmTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=gencode --include=mainAsm sizes ${asmReportTestFile} output/$@.sizes
	${diff} expected/$@.sizes output/$@.sizes

asmIdmapTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=refSeqAccn --toIdType=gencode idmap ${asmReportTestFile} output/$@.idmap
	${diff} expected/$@.idmap output/$@.idmap

asmIdmapMainAsmTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=ucscStyleName --toIdType=gencode --include=mainAsm idmap ${asmReportTestFile} output/$@.idmap
	${diff} expected/$@.idmap output/$@.idmap

asmIdmapMixedAsmTest: mkdirs
	${ncbiAssemblyReportConvert} --skipUnmapped --fromIdType=ucscStyleName --toIdType=sequenceNameGenbankAccn idmap ${asmReportTestFile} output/$@.idmap 2>output/$@.err
	${diff} expected/$@.idmap output/$@.idmap
	${diff} expected/$@.err output/$@.err

asmUmappedErrTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=ucscStyleName --toIdType=sequenceNameGenbankAccn idmap ${asmReportTestFile} output/$@.idmap 2>output/$@.err || true
	${diff} expected/$@.err output/$@.err

clintChimpAgp = input/GCA_002880755.3.chr10.comp.agp$
grch38Agp = ${ncbiTestInputDir}/GCA_000001305.2.chr22.agp

agpToPslTests: agpToPslBasicTest agpToPslLocalCompTest agpToPslSkipTest agpToPslGapsTest

agpToPslBasicTest: mkdirs
	${agpToPsl} ${clintChimpAgp} output/$@.psl
	pslCheck output/$@.psl
	${diff} expected/$@.psl output/$@.psl

agpToPslLocalCompTest: mkdirs
	${agpToPsl} --componentSizes=input/Clint_Chimp.chroms --componentLocalId2Acc=input/Clint_Chimp.component_localID2acc ${clintChimpAgp} output/$@.psl
	pslCheck output/$@.psl
	${diff} expected/$@.psl output/$@.psl

agpToPslSkipTest: mkdirs
	${agpToPsl} --skipUnmappable --componentSizes=input/Clint_Chimp.skip.chroms --componentLocalId2Acc=input/Clint_Chimp.skip.component_localID2acc ${clintChimpAgp} output/$@.psl >output/$@.out 2>&1
	pslCheck output/$@.psl
	${diff} expected/$@.psl output/$@.psl
	${diff} expected/$@.out output/$@.out

agpToPslGapsTest: mkdirs
	${agpToPsl} ${grch38Agp} output/$@.psl
	pslCheck output/$@.psl
	${diff} expected/$@.psl output/$@.psl

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
