# Copyright 2006-2025 Mark Diekhans
"""Miscellaneous command line parsing operations"""
from pycbio.sys.objDict import ObjDict

def getOptionalArgs(parser, args):
    """Get the parse command line option arguments (-- or - options) as an
    object were the options are fields in the object.  Useful for packaging up
    a large number of options to pass around."""

    opts = ObjDict()
    for act in parser._actions:
        if (len(act.option_strings) > 0) and (act.dest != 'help'):
            setattr(opts, act.dest, getattr(args, act.dest))
    return opts

def parse(parser):
    """call argparse parse_args and return (opts, args)"""
    args = parser.parse_args()
    return getOptionalArgs(parser, args), args
