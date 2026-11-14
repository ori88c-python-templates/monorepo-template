"""Print the installed apps that have a Dockerfile."""

from __future__ import annotations

from collections.abc import Sequence

from helpers.directory_lists import apps_with_dockerfile, run_lister


def main(argv: Sequence[str] | None = None) -> None:
    """Print the app image list as JSON, and append it for GitHub Actions.

    Args:
        argv: CLI arguments. ``None`` reads the process arguments.
    """
    run_lister(
        prog="list_app_images.py",
        description="Print the apps under python/apps that have a Dockerfile.",
        output_name="apps",
        lister=apps_with_dockerfile,
        argv=argv,
    )


if __name__ == "__main__":
    main()
