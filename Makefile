root = .
include ${root}/defs.mk


PKGS =  pycbio.align pycbio.distrib pycbio.exrun pycbio.hgbrowser pycbio.hgdata \
	pycbio.html pycbio.ncbi pycbio.stats pycbio.sys pycbio.tsv

PROGS = clusterGenesSelect genePredFlatten ncbiGbFetch clusterGenesStats \
	genePredSelect profStats gbffGenesToGenePred jsonDumpKeyStructure tsvSelectById \
	geneCheckStats ncbiAssemblyReportConvert vennChart csvToTsv

all: libcomp

libcomp:
	PYTHONPATH=lib ${PYTHON} -m compileall -l $(subst .,/,${PKGS})

test:
	(cd tests && ${MAKE} test PYTHON=python3)
	(cd tests && ${MAKE} test PYTHON=python2)

lint:
	${FLAKE8} lib/pycbio tests/libtests ${PROGS:%=bin/%}

clean:
	(cd tests && ${MAKE} clean)
	find lib tests -name '*.pyc' -exec rm -f '{}' ';'
	find lib -depth -name '__pycache__' -exec rm -rf '{}' ';'
