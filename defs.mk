# include with
#   root=../..
#   include ${root}/defs.mk

PYTHON = python3
FLAKE8 = python3 -m flake8

export PYTHONPATH:=${root}/lib:${PYTHONPATH}
ifeq (${PYTHONWARNINGS},)
   # set to error to find were they are coming from
   export PYTHONWARNINGS=always
endif

binDir = ${root}/bin
diff = diff -u

