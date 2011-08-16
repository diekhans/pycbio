
VPATH = src/progs/tsv:src/progs/gbff:src/progs/genePred:src/progs/loci:src/progs/ncbi:src/progs/geneCheck:src/progs/profStats:src/progs/vennChart
BIN_PROGS = \
	bin/tsvSelectById \
	bin/gbffGenesToGenePred \
	bin/clusterGenesStats \
	bin/clusterGenesSelect \
	bin/genePredSelect \
	bin/ncbiGbFetch \
	bin/geneCheckStats \
	bin/profStats \
	bin/vennChart

progsWithTests = gbff ncbi

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

test:  libTests ${progsWithTests:%=%.progtest}

libTests:
	(cd src/lib && ./runTests)

%.progtest:
	(cd src/progs/$*/tests && ${MAKE} test)

clean:
	rm -rf bin
	rm -f lib
	find src/lib -name '*.pyc' -exec rm -f '{}' \;

# update the two UCSC trees in /hive/groups
ucscUpdate: recon.ucscUpdate gencode.ucscUpdate

%.ucscUpdate:
	(cd /hive/groups/$*/local/pycbio && svn up && make)
