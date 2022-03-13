root = ../../..
include ${root}/defs.mk

export PYTHONPATH

emblToFasta = ${binDir}/emblToFasta

test: dfamTest dfamNmTest example1Test

dfamTest: mkdirs
	${emblToFasta} input/Dfam.embl output/$@.fa
	${diff} expected/$@.fa output/$@.fa

dfamNmTest: mkdirs
	${emblToFasta} --idNM input/Dfam.embl output/$@.fa
	${diff} expected/$@.fa output/$@.fa

example1Test: mkdirs
	${emblToFasta} input/example1.embl output/$@.fa
	${diff} expected/$@.fa output/$@.fa

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
