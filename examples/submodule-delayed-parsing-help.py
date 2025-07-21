###
# As of Python 3.13.5, help doesn't work with delayed configuration of subparser.
# the below code works around this
#
# problem examlle
#
#    % python delay-summodules.py  --help  align
#    usage: flair [-h] [--kirk] {align} ...
#
#    positional arguments:
#      {align}
#        align     align reads
#
#    options:
#      -h, --help  show this help message and exit
#      --kirk
#
#    % python delay-summodules.py  align   --help
#    usage: flair align [-h]
#
#    options:
#      -h, --help  show this help message and exit
#


import argparse
import sys

class SilentExitParser(argparse.ArgumentParser):
    def error(self, message):
        # Suppress error on first pass
        raise argparse.ArgumentError(None, message)

    def exit(self, status=0, message=None):
        raise argparse.ArgumentError(None, message or "")

def make_common_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--kirk", action="store_true", help="Enable Kirk mode")
    return common

def main(argv=None):
    argv = argv or sys.argv[1:]

    # Step 1: Dummy parse just to extract known_args.cmd, safely
    dummy = SilentExitParser(add_help=False, parents=[make_common_args()])
    dummy_sub = dummy.add_subparsers(dest="cmd", required=True)
    dummy_sub.add_parser("align", add_help=False)

    try:
        known_args, _ = dummy.parse_known_args(argv)
        subcmd = known_args.cmd
    except argparse.ArgumentError:
        subcmd = None  # fall through to full parser

    # Step 2: Build real parser with full help support
    parser = argparse.ArgumentParser(prog="flair", parents=[make_common_args()])
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    if subcmd == "align":
        align = subparsers.add_parser("align", parents=[make_common_args()])
        align.add_argument("--reads", required=True, help="Input reads file")
        align.add_argument("--genome", required=True, help="Genome reference")

    args = parser.parse_args(argv)
    print(args)

if __name__ == "__main__":
    main()
