
PYTHON = python

PKGS =  pycbio.align pycbio.distrib pycbio.exrun pycbio.hgbrowser pycbio.hgdata \
	pycbio.html pycbio.ncbi pycbio.stats pycbio.sys pycbio.tsv

PROGS = clusterGenesSelect genePredFlatten ncbiGbFetch clusterGenesStats \
	genePredSelect profStats gbffGenesToGenePred jsonDumpKeyStructure tsvSelectById \
	geneCheckStats ncbiAssemblyReportConvert vennChart csvToTsv

all: libcomp

libcomp:
	PYTHONPATH=lib ${PYTHON} -m compileall -l $(subst .,/,${PKGS})

test:
	(cd tests && ${MAKE} test)

lint:
	flake8 lib/pycbio tests/libtests ${PROGS:%=bin/%}

clean:
	(cd tests && ${MAKE} clean)
