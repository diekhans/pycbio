# include with
#   root=../..
#   include ${root}/defs.mk

PYTHON = python3
FLAKE8 = python3 -m flake8

export PYTHONPATH:=${root}/lib:${PYTHONPATH}
export PYTHONWARNINGS=always

binDir = ${root}/bin
diff = diff -u

