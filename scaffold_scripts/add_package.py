"""Create an empty shared package and register it in the workspace."""

import argparse
from collections.abc import Sequence

from helpers.cli import fail, succeed
from helpers.errors import ScaffoldError
from helpers.package_operations import add_package
from helpers.paths import RepoPaths
from helpers.sync import Sync


def main(
    argv: Sequence[str] | None = None, *, paths: RepoPaths | None = None, sync: Sync | None = None
) -> None:
    """Add one package.

    Args:
        argv: Positional argument, the import name. ``None`` reads the process
            arguments.
        paths: Repository locations. ``None`` discovers them from this file.
        sync: Lock step. ``None`` runs uv.
    """
    parser = argparse.ArgumentParser(
        prog="add_package.py",
        description="Create an empty package under python/packages and register it.",
    )
    parser.add_argument("import_name")
    args = parser.parse_args(argv)
    try:
        message = add_package(paths or RepoPaths.discover(), args.import_name, sync=sync)
    except ScaffoldError as exc:
        fail(exc)
    succeed(message)


if __name__ == "__main__":
    main()
