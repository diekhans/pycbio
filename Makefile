
PYTHON = python

PKGS =  pycbio.align pycbio.distrib pycbio.exrun pycbio.hgbrowser pycbio.hgdata \
	pycbio.html pycbio.ncbi pycbio.stats pycbio.sys pycbio.tsv


all: libcomp

libcomp:
	PYTHONPATH=. ${PYTHON} -m compileall -l $(subst .,/,${PKGS})

test:
	(cd tests && ${MAKE} test)

pylint:
	PYTHONPATH=src/lib pylint --rcfile=pylint.cfg $(subst .,/,${PKGS})

clean:
	(cd tests && ${MAKE} clean)
