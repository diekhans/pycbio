root = ..
include ${root}/defs.mk

subdirs = libtests progtests

all:

test: ${subdirs:%=%.test}

libtests.test:
	pytest libtests 

progtests.test:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)
