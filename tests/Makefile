root = ..
include ${root}/defs.mk

subdirs = libtests progtests

all:

test: ${subdirs:%=%.test}

libtests.test:
	${PYTHON} ./runTests

progtests.test:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)
