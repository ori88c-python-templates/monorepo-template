"""Print the blueprint categories under python/_templates."""

from __future__ import annotations

from collections.abc import Sequence

from helpers.directory_lists import blueprint_categories, run_lister


def main(argv: Sequence[str] | None = None) -> None:
    """Print the category list as JSON, and append it for GitHub Actions.

    Args:
        argv: CLI arguments. ``None`` reads the process arguments.
    """
    run_lister(
        prog="list_blueprints.py",
        description="Print the blueprint directories under python/_templates.",
        output_name="categories",
        lister=blueprint_categories,
        argv=argv,
    )


if __name__ == "__main__":
    main()
