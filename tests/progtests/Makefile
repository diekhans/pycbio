root = ../..
include ${root}/defs.mk

subdirs = gbff geneCheck ncbi csvToTsv \
	bedCmdTests pslLoadSqlLite conversion utf8ToAscii \
	spliceJuncs

slow_subdirs = sra

all_subdirs = ${subdirs} ${slow_subdirs}

# FIXME: not done: vennChart

all:

test: ${subdirs:%=%.test}
%.test:
	(cd $* && ${MAKE} test)

test-slow: ${slow_subdirs:%=%.test-slow}
%.test-slow:
	(cd $* && ${MAKE} test-slow)


clean: ${all_subdirs:%=%.clean}

%.clean:
	(cd $* && ${MAKE} clean)
