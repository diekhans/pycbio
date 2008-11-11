
VPATH = src/progs/tsv:src/progs/gbff:src/progs/genePred:src/progs/loci:src/progs/ncbi:src/progs/geneCheck
BIN_PROGS = \
	bin/tsvSelectById \
	bin/gbffGenesToGenePred \
	bin/clusterGenesStats \
	bin/clusterGenesSelect \
	bin/genePredSelect \
	bin/ncbiGbFetch \
	bin/geneCheckStats

all: lib ${BIN_PROGS}


lib:
	ln -sf src/lib lib

bin/%: %
	@mkdir -p bin
	ln -sf ../$< $@

test:
	(cd src/lib && ./runTests)

clean:
	rm -rf bin
	rm -f lib
