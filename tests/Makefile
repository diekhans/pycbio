root = ..
include ${root}/defs.mk

export PYTHONPATH:=${root}/lib:libtests:${PYTHONPATH}

# override number of process with nproc=0 to run
# in main process.
# stdout not echo with mulitple processes
nproc = 20

# logging level
loglevel = INFO

# override with pytest_extra=-v or what ever
pytest_extra = 

# to get less verbose traceback
traceback = --tb=native

# used to find source of ResourceWarning
# export PYTHONTRACEMALLOC = 20

subdirs = libtests progtests

all:

test: ${subdirs:%=%}

.PHONY: libtests
libtests:
	${PYTEST} --capture=no ${traceback} --numprocesses=${nproc} --log-cli-level=${loglevel} ${pytest_extra} libtests 

.PHONY: progtests
progtests:
	(cd progtests && ${MAKE} test)

clean:
	(cd progtests && ${MAKE} clean)
	rm -rf libtests/pycbio/*/output
