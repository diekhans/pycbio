root = ../../..
include ${root}/defs.mk

export PYTHONPATH

ncbiGbFetch = ${runBin}/ncbiGbFetch
ncbiAssemblyReportConvert = ${runBin}/ncbiAssemblyReportConvert


# refseq mRNAs, ESTs
testAccver = NM_013266.2 AK289756.1 BG187649.1 U14680.1

diff = diff -u

# if there is no domain configured, we need to for an email address for ncbiGbFetch
ifeq ($(findstring .,$(shell hostname -f)),)
   email = --email=markd@ucsc.edu
endif


test: fetchTests asmReportCnvTests

fetchTests: gbffFetchTest faFetchTest

gbffFetchTest: mkdirs
	${ncbiGbFetch} ${email} --out=output/$@.gbff ${testAccver}
	${diff} expected/$@.gbff output/$@.gbff

faFetchTest: mkdirs
	${ncbiGbFetch} ${email} --fasta --out=output/$@.fa ${testAccver}
	${diff} expected/$@.fa output/$@.fa

asmReportCnvTests: asmSeqNameUcscLiftTest asmRefSeqGencodeLiftTest asmSeqNameSizesTest \
	asmGencodeNameSizesMainChromsTest asmGencodeNameSizesMainAsmTest \
	asmIdmapTest asmIdmapMainAsmTest asmIdmapMixedAsmTest

asmReportTestFile = ../../libtests/pycbio/ncbi/input/GCF_000001405.28.assembly.txt

asmSeqNameUcscLiftTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=sequenceName --toIdType=ucscStyleName lift ${asmReportTestFile} output/$@.lift
	${diff} expected/$@.lift output/$@.lift

asmRefSeqGencodeLiftTest: mkdirs
	${ncbiAssemblyReportConvert} --fromIdType=refSeqAccn --toIdType=gencode lift ${asmReportTestFile} output/$@.lift
	${diff} expected/$@.lift output/$@.lift

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
	${ncbiAssemblyReportConvert} --fromIdType=ucscStyleName --toIdType=sequenceNameGenbankAccn idmap ${asmReportTestFile} output/$@.idmap
	${diff} expected/$@.idmap output/$@.idmap

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
