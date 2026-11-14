"""Package import names, directories, and distribution names."""

import re
from dataclasses import dataclass
from typing import Final

from helpers.errors import ScaffoldError

_IDENTIFIER: Final = re.compile(r"^[a-z][a-z0-9_]*$")
_SHARED_PREFIX: Final = "shared_"


@dataclass(frozen=True)
class PackageIdentity:
    """One shared package, in the spellings the repo uses for it.

    ``import_name`` is the installed module. ``directory`` is
    ``python/packages/<directory>``. A leading ``shared_`` is not part of
    that directory. ``distribution_name`` is the uv project name.
    """

    import_name: str
    directory: str
    distribution_name: str


def identity_for_new_package(import_name: str) -> PackageIdentity:
    """Return the identity a new package gets from its import name.

    A leading ``shared_`` is stripped once for the directory. The
    distribution name replaces ``_`` with ``-``.

    Raises:
        ScaffoldError: The import name is not a lowercase identifier, or
            stripping ``shared_`` leaves no directory name.
    """
    checked = require_import_name(import_name)
    if checked.startswith(_SHARED_PREFIX):
        directory = checked.removeprefix(_SHARED_PREFIX)
    else:
        directory = checked
    if _IDENTIFIER.fullmatch(directory) is None:
        raise ScaffoldError(_invalid_import(import_name))
    return PackageIdentity(
        import_name=checked,
        directory=directory,
        distribution_name=checked.replace("_", "-"),
    )


def require_import_name(import_name: str) -> str:
    """Return ``import_name`` when it can be a module name.

    Raises:
        ScaffoldError: The name is not a lowercase identifier.
    """
    if _IDENTIFIER.fullmatch(import_name) is None:
        raise ScaffoldError(_invalid_import(import_name))
    return import_name


def _invalid_import(import_name: str) -> str:
    return f"Package import name {import_name!r} must match {_IDENTIFIER.pattern}."
