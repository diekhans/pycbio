root = ..
include ${root}/defs.mk

export PYTHONPATH:=${root}/lib:libtests:${PYTHONPATH}

subdirs = libtests progtests

all:

test: ${subdirs:%=%.test}

libtests.test:
	pytest --capture=no libtests 

progtests.test:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)
