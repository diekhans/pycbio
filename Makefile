root = .
include ${root}/defs.mk

bin_progs = $(wildcard bin/*)
test_bin_progs = $(wildcard tests/bin/* tests/libtests/pycbio/sys/bin/*)
all_progs = ${bin_progs} ${test_bin_progs}
pyprogs = $(shell file -F '	' ${all_progs} | awk '/Python script/{print $$1}')

all: libcomp

libcomp:
	PYTHONPATH=lib ${PYTHON} -m compileall -l lib/pycbio lib/pycbio/*

test:
	cd tests && ${MAKE} test

test-full:
	cd tests && ${MAKE} test-full

libtest:
	cd tests && ${MAKE} libtest

progtest:
	cd tests && ${MAKE} progtest

lint:
	${FLAKE8} --color=never lib/pycbio tests/libtests ${pyprogs}

clean:
	(cd tests && ${MAKE} clean)
	find lib tests -name '*.pyc' -exec rm -f '{}' ';'
	find lib -depth -name '__pycache__' -exec rm -rf '{}' ';'
	rm -rf dist build pycbio.egg-info lib/pycbio.egg-info
