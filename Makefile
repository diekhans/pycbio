root = .
include ${root}/defs.mk


pyprogs = $(shell file -F '	' bin/* tests/*/bin/* | awk '/Python script/{print $$1}')

all: libcomp

libcomp:
	PYTHONPATH=lib ${PYTHON} -m compileall -l lib/pycbio lib/pycbio/*

test:
	cd tests && ${MAKE} test

lint:
	${FLAKE8} --color=never lib/pycbio tests/libtests ${pyprogs}

clean:
	(cd tests && ${MAKE} clean)
	find lib tests -name '*.pyc' -exec rm -f '{}' ';'
	find lib -depth -name '__pycache__' -exec rm -rf '{}' ';'
