root = ../..
include ${root}/defs.mk

subdirs = gbff geneCheck ncbi csvToTsv bedCmdTests pslLoadSqlLite conversion utf8ToAscii
# FIXME: not done: vennChart

all:

test: ${subdirs:%=%.test}

%.test:
	(cd $* && ${MAKE} test)

clean: ${subdirs:%=%.clean}

%.clean:
	(cd $* && ${MAKE} clean)
