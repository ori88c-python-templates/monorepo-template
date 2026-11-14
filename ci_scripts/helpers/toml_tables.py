"""Read TOML tables and dependency lists without losing their types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from helpers.errors import SelectionError


@dataclass(frozen=True)
class RequirementGroup:
    """One optional-dependency or dependency-group entry.

    ``requirements`` is the group's requirement strings, sorted.
    """

    name: str
    requirements: tuple[str, ...]


def object_dict(value: object) -> dict[str, object] | None:
    """Return ``value`` as a string-keyed table.

    Args:
        value: A TOML value.

    Returns:
        The table, or ``None`` when ``value`` is not a table.
    """
    if not isinstance(value, dict):
        return None
    table = cast("dict[object, object]", value)
    return {str(key): item for key, item in table.items()}


def object_list(value: object) -> list[object] | None:
    """Return ``value`` as a list of TOML values.

    Args:
        value: A TOML value.

    Returns:
        The list, or ``None`` when ``value`` is not a list.
    """
    if not isinstance(value, list):
        return None
    return cast("list[object]", value)


def requirement_strings(value: object) -> tuple[str, ...]:
    """Return the requirement strings in one dependency list.

    An absent list is empty. The strings are stripped and sorted, so a reorder
    is not a difference. Extras and version specs stay in the string.

    Args:
        value: A TOML dependency array, or ``None`` when the key is absent.

    Returns:
        The requirement strings.

    Raises:
        SelectionError: ``value`` is not a list of strings.
    """
    if value is None:
        return ()
    items = object_list(value)
    if items is None:
        raise SelectionError("A dependency list is not a list of strings.")
    strings: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise SelectionError("A dependency list is not a list of strings.")
        strings.append(item.strip())
    requirement_strings_asc_by_text = tuple(sorted(strings))
    return requirement_strings_asc_by_text  # noqa: RET504


def requirement_groups(value: object) -> tuple[RequirementGroup, ...]:
    """Return each group's name and its requirement strings.

    Args:
        value: An ``optional-dependencies`` or ``dependency-groups`` table,
            or ``None`` when the table is absent.

    Returns:
        Groups sorted by name. An absent table is empty.

    Raises:
        SelectionError: ``value`` is not a table of string lists.
    """
    if value is None:
        return ()
    table = object_dict(value)
    if table is None:
        raise SelectionError("A dependency group table is not a table.")
    groups = [RequirementGroup(name, requirement_strings(item)) for name, item in table.items()]
    groups_asc_by_name = tuple(sorted(groups, key=lambda group: group.name))
    return groups_asc_by_name  # noqa: RET504
