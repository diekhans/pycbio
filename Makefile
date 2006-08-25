
VPATH = src/progs/tsv:src/progs/gbff:src/progs/loci:src/progs/ncbi:src/progs/geneCheck
BIN_PROGS = \
	bin/tsvSelectById \
	bin/gbffGenesToGenePred \
	bin/clusterGenesStats \
	bin/clusterGenesSelect \
	bin/ncbiGbFetch \
	bin/geneCheckStats

all: lib ${BIN_PROGS}


lib:
	ln -sf src/lib lib

bin/%: %
	@mkdir -p bin
	ln -sf ../$< $@

clean:
	rm -rf bin
	rm -f lib
