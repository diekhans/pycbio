
export PYTHONPATH=../../..
binDir = ../../../bin
ncbiGbFetch = ${binDir}/ncbiGbFetch
ncbiAssemblyReportConvert = ${binDir}/ncbiAssemblyReportConvert
diff = diff -u

# refseq mRNAs, ESTs
testAccver = NM_013266.2 AK289756.1 BG187649.1 U14680.1

test: fetchTests asmReportCnvTests

fetchTests: gbffFetchTest faFetchTest

gbffFetchTest: mkdirs
	${ncbiGbFetch} --out=output/$@.gbff ${testAccver}
	${diff} expected/$@.gbff output/$@.gbff

faFetchTest: mkdirs
	${ncbiGbFetch} --fasta --out=output/$@.fa ${testAccver}
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
