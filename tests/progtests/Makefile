subdirs = gbff geneCheck ncbi
# FIXME: not done: vennChart

all:

test: ${subdirs:%=%.test}

%.test:
	(cd $* && ${MAKE} test)

clean: ${subdirs:%=%.clean}

%.clean:
	(cd $* && ${MAKE} clean)

