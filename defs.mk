# include with
#   root=../..
#   include ${root}/defs.mk

PYTHON = python3
FLAKE8 = flake8

export PYTHONPATH:=${rootDir}/lib:${PYTHONPATH}

binDir = ${root}/bin
diff = diff -u

# prefix commmand to run with this to pickup python versions
runBin = ${PYTHON} ${binDir}
