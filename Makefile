
PYTHON = python

PKGS =  pycbio.align pycbio.distrib pycbio.exrun pycbio.hgbrowser pycbio.hgdata \
	pycbio.html pycbio.ncbi pycbio.stats pycbio.sys pycbio.tsv


all: libcomp

libcomp:
	PYTHONPATH=lib ${PYTHON} -m compileall -l $(subst .,/,${PKGS})

test:
	(cd tests && ${MAKE} test)

lint:
	flake8 lib/pycbio tests/libtests

pylint:
	PYTHONPATH=lib pylint --rcfile=pylint.cfg $(subst .,/,${PKGS})

clean:
	(cd tests && ${MAKE} clean)
