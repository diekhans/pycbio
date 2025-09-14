root = ..
include ${root}/defs.mk

export PYTHONPATH:=${root}/lib:libtests:${PYTHONPATH}

# keep pytest xdist from complaining about the terminal
export TERM=dumb

# override number of process with nproc=0 to run
# in main process.
# stdout not echo with mulitple processes
nproc = 20

# logging level
loglevel = INFO

# override with pytest_extra=-v or what ever
pytest_extra = 

# standard traceback, less decoration, but lots pytest internal
traceback = --tb=native

# used to find source of ResourceWarning
# export PYTHONTRACEMALLOC = 20

all: libtest progtest

test: libtest progtest

.PHONY: libtest
libtest: common-data
	${PYTEST} --capture=no ${traceback} --numprocesses=${nproc} --log-cli-level=${loglevel} ${pytest_extra} libtests 

.PHONY: progtest
progtest: common-data
	(cd progtests && ${MAKE} test)

common-data: common-output/grch38-regions.fa.gz.fai common-output/grch38-regions.2bit

common-output/grch38-regions.fa.gz.fai: common-output/grch38-regions.fa.gz
	samtools faidx $<

common-output/grch38-regions.fa.gz: data/grch38-regions.fa
	mkdir -p $(dir $@)
	bgzip -c $< >$@

common-output/grch38-regions.2bit: data/grch38-regions.fa
	faToTwoBit $< $@

clean:
	(cd progtests && ${MAKE} clean)
	rm -rf libtests/pycbio/*/output common-output

