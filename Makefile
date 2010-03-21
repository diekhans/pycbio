
VPATH = src/progs/tsv:src/progs/gbff:src/progs/genePred:src/progs/loci:src/progs/ncbi:src/progs/geneCheck:src/progs/profStats
BIN_PROGS = \
	bin/tsvSelectById \
	bin/gbffGenesToGenePred \
	bin/clusterGenesStats \
	bin/clusterGenesSelect \
	bin/genePredSelect \
	bin/ncbiGbFetch \
	bin/geneCheckStats \
	bin/profStats

PKGS =  pycbio.align pycbio.distrib pycbio.exrun pycbio.hgbrowser pycbio.hgdata \
	pycbio.html pycbio.ncbi pycbio.stats pycbio.sys pycbio.tsv


all: lib libcomp ${BIN_PROGS}

lib:
	ln -sf src/lib lib

libcomp:
	PYTHONPATH=src/lib python -m compileall -l $(subst .,/,${PKGS:%=src/lib/%})

bin/%: %
	@mkdir -p bin
	ln -sf ../$< $@

test:
	(cd src/lib && ./runTests)

clean:
	rm -rf bin
	rm -f lib
	find src/lib -name '*.pyc' -exec rm -f '{}' \;
