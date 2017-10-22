# include with
#   root=../..
#   include ${root}/defs.mk

PYTHON = python2

binDir = ${root}/bin
diff = diff -u

# prefix commmand to run with this to pickup python versions
runBin = ${PYTHON} ${binDir}
