subdirs = libtests progtests

all:

test: ${subdirs:%=%.test}

libtests.test:
	./runTests

progtests.test:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)

