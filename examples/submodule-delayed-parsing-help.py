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

def make_common_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--kirk", action="store_true", help="Enable Kirk mode")
    return common

def main():
    # Step 1: pre-parse just to extract known_args.cmd, safely
    pre_parser = argparse.ArgumentParser(add_help=False, parents=[make_common_args()], exit_on_error=False)
    pre_parser_sub = pre_parser.add_subparsers(dest="cmd", required=True)
    pre_parser_sub.add_parser("align", add_help=False)

    try:
        known_args, _ = pre_parser.parse_known_args()
        subcmd = known_args.cmd
    except argparse.ArgumentError:
        subcmd = None  # fall through to full parser
    print(f"@ Step 1: {subcmd}", file=sys.stderr)

    # Step 2: Build real parser with full help support
    parser = argparse.ArgumentParser(prog="flair", parents=[make_common_args()])
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    subparsers.add_parser("align", parents=[make_common_args()])
    print("@ Step 2: parser built", file=sys.stderr)

    if subcmd == "align":
        align = subparsers.choices["align"]
        align.add_argument("--reads", required=True, help="Input reads file")
        align.add_argument("--genome", required=True, help="Genome reference")
        print("@ Step 3: subparser initalized", file=sys.stderr)

    args = parser.parse_args()
    print(args, file=sys.stderr)

main()
