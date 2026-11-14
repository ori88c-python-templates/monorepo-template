"""Distribution names as PEP 508 requirements spell them."""

import re
from typing import Final

_NAME: Final = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")


def normalize_distribution(name: str) -> str:
    """Return the packaging-normalized form of a distribution name.

    Args:
        name: A ``project.name`` or a requirement name.

    Returns:
        Lowercase, with runs of ``-``, ``_``, and ``.`` collapsed to ``-``.
    """
    return re.sub(r"[-_.]+", "-", name).strip("-").lower()


def requirement_name(requirement: str) -> str:
    """Return the normalized distribution name a requirement string names.

    Args:
        requirement: One dependency string, extras, version spec, and
            marker included.

    Returns:
        The normalized name, or an empty string when none can be read.
    """
    text = requirement.split(";", 1)[0].strip().split("[", 1)[0].strip()
    match = _NAME.match(text)
    if match is None:
        return ""
    return normalize_distribution(match.group(0))


def split_requirement(requirement: str) -> tuple[str, str] | None:
    """Split a requirement into its raw name and everything after it.

    Args:
        requirement: One dependency string, already stripped.

    Returns:
        The name as written and the remainder, or ``None`` when the string
        does not start with a distribution name.
    """
    match = _NAME.match(requirement)
    if match is None:
        return None
    return match.group(0), requirement[match.end() :]
