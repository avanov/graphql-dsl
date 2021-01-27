import argparse
import json
import sys
from pathlib import Path
from typing import Mapping
from itertools import islice

from .. import parser


def is_empty_dir(p: Path) -> bool:
    return p.is_dir() and not bool(list(islice(p.iterdir(), 1)))


def setup(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    sub = subparsers.add_parser('gen', help='Generate Python definitions from GraphQL schema source.')
    sub.add_argument('-s', '--source', help="Path to a GraphQL schema file. "
                                            "If not specified, then the data will be read from stdin.")
    sub.add_argument('-o', '--out-dir', required=True,
                     help="Output directory that will contain a newly generated Python client.")
    sub.add_argument('-n', '--name', required=True,
                     help="Name of a newly generated Python client (package name).")
    sub.add_argument('-f', '--force-overwrite', required=False, action='store_true',
                     help="Overwrite existing files and directories if they already exist"
                     )
    sub.set_defaults(run_cmd=main)
    return sub


def main(args: argparse.Namespace, in_channel=sys.stdin, out_channel=sys.stdout) -> None:
    """ $ <cmd-prefix> gen <source> <target>
    """
    try:
        src = Path(args.source).read_text()
    except TypeError:
        # source is None, read from stdin
        src = in_channel.read()

    spec = parser.parse(src)


    out_channel.write('Successfully parsed.\n')

