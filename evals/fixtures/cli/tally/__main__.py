"""Command-line entry point: ``python3 -m tally report <file>``."""

import argparse
import sys
from datetime import date

from tally.loader import LoadError, load
from tally.summary import summarize
from tally.table import format_table


def _day(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must look like 2026-01-31")


def build_parser():
    parser = argparse.ArgumentParser(prog="tally", description="Summarise expense CSV files.")
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report", help="print a summary by category")
    report.add_argument("file", help="path to the expenses CSV")
    report.add_argument("--since", type=_day, metavar="DATE", help="only count entries from this day on")
    return parser


def run_report(args, out):
    summary = summarize(load(args.file), since=args.since)
    out.write(format_table(summary) + "\n")
    return 0


def main(argv=None, out=sys.stdout, err=sys.stderr):
    args = build_parser().parse_args(argv)
    try:
        return run_report(args, out)
    except LoadError as exc:
        err.write(f"tally: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
