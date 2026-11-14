"""Rename a shared package's directory, import, and distribution."""

import argparse
from collections.abc import Sequence

from helpers.cli import fail, succeed
from helpers.errors import ScaffoldError
from helpers.package_operations import rename_package
from helpers.paths import RepoPaths
from helpers.sync import Sync


def main(
    argv: Sequence[str] | None = None, *, paths: RepoPaths | None = None, sync: Sync | None = None
) -> None:
    """Rename one package.

    Args:
        argv: Positional arguments, source import name then target import name.
            ``None`` reads the process arguments.
        paths: Repository locations. ``None`` discovers them from this file.
        sync: Lock step. ``None`` runs uv.
    """
    parser = argparse.ArgumentParser(
        prog="rename_package.py",
        description="Rename a package's directory, import name, and distribution name.",
    )
    parser.add_argument("source")
    parser.add_argument("target")
    args = parser.parse_args(argv)
    try:
        message = rename_package(
            paths or RepoPaths.discover(),
            args.source,
            args.target,
            sync=sync,
        )
    except ScaffoldError as exc:
        fail(exc)
    succeed(message)


if __name__ == "__main__":
    main()
