root = ..
include ${root}/defs.mk

subdirs = libtests progtests

all:

test: ${subdirs:%=%.test}

libtests.test:
	${PYTHON3} ./runTests

progtests.test:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)
