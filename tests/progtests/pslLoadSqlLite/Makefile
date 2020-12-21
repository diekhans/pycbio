root = ../../..
include ${root}/defs.mk

export PYTHONPATH

pslLoadSqlLite = ${binDir}/pslLoadSqlLite

testPsl = ../../libtests/pycbio/hgdata/input/pslTest.psl

test: testBasicLoad

testBasicLoad: mkdirs
	${pslLoadSqlLite} ${testPsl} output/$@.db refSeqAln
	sqlite3 output/$@.db 'SELECT * FROM refSeqAln' | cut -f 2- >output/$@.out.psl
	${diff} expected/$@.out.psl output/$@.out.psl

mkdirs:
	@mkdir -p output

clean:
	rm -rf output
