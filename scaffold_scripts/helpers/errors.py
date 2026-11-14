"""Failures a scaffold command reports and then stops."""

from collections.abc import Sequence


class ScaffoldError(Exception):
    """The command cannot continue.

    The message is the whole report. Callers print it and exit.
    """


def already_exists_message(name: str) -> str:
    """Return the duplicate-name failure."""
    return f"App '{name}' already exists at python/apps/{name}."


def missing_message(name: str) -> str:
    """Return the missing-app failure."""
    return f"App '{name}' does not exist."


def package_exists_at(import_name: str, directory: str) -> str:
    """Return the failure for a package directory that is already present."""
    return f"Package '{import_name}' already exists at python/packages/{directory}."


def package_exists(import_name: str) -> str:
    """Return the failure for an import or distribution that is already used."""
    return f"Package '{import_name}' already exists."


def package_missing(import_name: str) -> str:
    """Return the failure for an import name no package uses."""
    return f"Package '{import_name}' does not exist."


def package_required_by(import_name: str, names: Sequence[str]) -> str:
    """Return the failure for a package other members still use."""
    return f"Package '{import_name}' is still required by {', '.join(names)}."
