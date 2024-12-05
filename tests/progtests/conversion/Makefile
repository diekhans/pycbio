root = ../../..
include ${root}/defs.mk

export PYTHONPATH

emblToFasta = ${binDir}/emblToFasta
fastaSelect = ${binDir}/fastaSelect

test: dfamTests fastaSelectTests

dfamTests: dfamTest dfamNmTest example1Test

dfamTest: mkdirs
	${emblToFasta} input/Dfam.embl output/$@.fa
	${diff} expected/$@.fa output/$@.fa

dfamNmTest: mkdirs
	${emblToFasta} --idNM input/Dfam.embl output/$@.fa
	${diff} expected/$@.fa output/$@.fa

example1Test: mkdirs
	${emblToFasta} input/example1.embl output/$@.fa
	${diff} expected/$@.fa output/$@.fa


fastaSelectTests: testFastaSelectAll testFastaSelectSome

testFastaSelectAll: mkdirs
	${fastaSelect} input/gencode.v47.pc_translations.fa output/$@.fa
	${diff} expected/$@.fa output/$@.fa

testFastaSelectSome: mkdirs
	(echo ENSP00000409316.1; echo ENSP00000464657.1) > output/$@.select.ids
	${fastaSelect} --selectFile=output/$@.select.ids input/gencode.v47.pc_translations.fa output/$@.fa
	${diff} expected/$@.fa output/$@.fa

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
