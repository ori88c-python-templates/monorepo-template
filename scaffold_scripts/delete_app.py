"""Delete an installed app from the tree, the workspace, and the env example."""

import argparse
from collections.abc import Sequence

from helpers.cli import fail, succeed
from helpers.errors import ScaffoldError
from helpers.operations import Sync, delete_app
from helpers.paths import RepoPaths


def main(
    argv: Sequence[str] | None = None, *, paths: RepoPaths | None = None, sync: Sync | None = None
) -> None:
    """Delete one app.

    Args:
        argv: Positional argument, the app name. ``None`` reads the process
            arguments.
        paths: Repository locations. ``None`` discovers them from this file.
        sync: Lock step. ``None`` runs uv.
    """
    parser = argparse.ArgumentParser(
        prog="delete_app.py",
        description="Delete an app from the tree, the workspace, and the env example.",
    )
    parser.add_argument("name")
    args = parser.parse_args(argv)
    try:
        message = delete_app(paths or RepoPaths.discover(), args.name, sync=sync)
    except ScaffoldError as exc:
        fail(exc)
    succeed(message)


if __name__ == "__main__":
    main()
