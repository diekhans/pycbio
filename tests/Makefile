root = ..
include ${root}/defs.mk

subdirs = libtests progtests

all:

test: ${subdirs:%=%.test}

# right now, py3 and py2 test can't be run in parallel
libtests.test:
	${PYTHON3} ./runTests
	${PYTHON2} ./runTests

progtests.test:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)
