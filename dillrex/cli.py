from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .runtime import DillrexError, run_file, run_repl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dillrex",
        description="Run Dillrex .drx programs or open the Dillrex terminal.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a Dillrex file")
    run_parser.add_argument("file", type=Path, help="Path to a .drx file")
    run_parser.add_argument("program_args", nargs="*", help="Arguments passed to the Dillrex program")

    subparsers.add_parser("shell", help="Open the Dillrex terminal")
    parser.add_argument("--version", action="store_true", help="Show Dillrex version")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].lower().endswith(".drx"):
        try:
            run_file(Path(argv[0]), args=argv[1:], work_dir=Path.cwd())
            return 0
        except DillrexError as exc:
            print(f"Dillrex error: {exc}")
            return 1

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from . import __version__

        print(f"Dillrex {__version__}")
        return 0

    try:
        if args.command == "run":
            run_file(args.file, args=args.program_args)
            return 0
        if args.command == "shell":
            run_repl()
            return 0
        parser.print_help()
        return 0
    except DillrexError as exc:
        print(f"Dillrex error: {exc}")
        return 1
