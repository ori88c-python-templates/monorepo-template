"""Replace one package's names in Python, project files, and its README."""

import re
from pathlib import Path
from typing import Final

from helpers.names import identifier_boundary, replace_symbol
from helpers.package_names import PackageIdentity
from helpers.paths import iter_files, read_text, write_text
from helpers.requirements import normalize_distribution, split_requirement

_DIST_SECTIONS: Final = frozenset(
    {
        "[project]",
        "[project.optional-dependencies]",
        "[dependency-groups]",
        "[tool.uv.sources]",
    },
)


def rewrite_package_tree(
    python_dir: Path,
    package_dir: Path,
    source: PackageIdentity,
    target: PackageIdentity,
) -> list[tuple[Path, str]]:
    """Rewrite package names under ``python_dir``.

    Python files, every ``pyproject.toml``, and the package README are
    included. ``compose.yaml``, ``.env.example``, and ``.cursor`` are not.

    Returns:
        The previous text of each file that changed, in write order.
    """
    changed: list[tuple[Path, str]] = []
    for path in rewrite_paths(python_dir, package_dir):
        old = read_text(path)
        new = rewrite_file(path, old, package_dir, source, target)
        if new == old:
            continue
        write_text(path, new)
        changed.append((path, old))
    return changed


def rewrite_paths(python_dir: Path, package_dir: Path) -> list[Path]:
    """Return the files a package rename rewrites."""
    files = [
        path
        for path in iter_files(python_dir)
        if path.name == "pyproject.toml" or path.suffix == ".py"
    ]
    readme = package_dir / "README.md"
    if readme.is_file():
        files.append(readme)
    return files


def rewrite_file(
    path: Path,
    text: str,
    package_dir: Path,
    source: PackageIdentity,
    target: PackageIdentity,
) -> str:
    """Return ``text`` with ``source`` renamed to ``target``."""
    if path.name == "pyproject.toml":
        return rewrite_project(text, source, target)
    if path.suffix == ".py" or path == package_dir / "README.md":
        return rewrite_python(text, source, target)
    return text


def rewrite_project(text: str, source: PackageIdentity, target: PackageIdentity) -> str:
    """Rename paths, the import, and the distribution in one project file.

    The ``packages/<directory>`` segment is replaced first, so a directory
    that is also the import name is not rewritten twice. When those two
    source names are the same token, dependency and project-name slots are
    then set to the new distribution name.
    """
    text = replace_package_path(text, source.directory, target.directory)
    text = replace_import_name(text, source.import_name, target.import_name)
    if source.distribution_name == source.import_name:
        return _retarget_distribution(text, target)
    return replace_symbol(text, source.distribution_name, target.distribution_name)


def rewrite_python(text: str, source: PackageIdentity, target: PackageIdentity) -> str:
    """Rename paths, the import, and the distribution in Python or a README."""
    text = replace_package_path(text, source.directory, target.directory)
    text = replace_import_name(text, source.import_name, target.import_name)
    if source.distribution_name == source.import_name:
        return text
    return replace_symbol(text, source.distribution_name, target.distribution_name)


def replace_package_path(text: str, old: str, new: str) -> str:
    """Replace the ``packages/<old>`` path segment with ``packages/<new>``."""
    if old == new:
        return text
    pattern = re.compile(rf"(?<=packages/){re.escape(old)}(?=/|\"|$)")
    return pattern.sub(new, text)


def replace_import_name(text: str, old: str, new: str) -> str:
    """Replace ``old`` except where it is the ``packages/<old>`` segment."""
    if old in {new, ""}:
        return text
    pattern = re.compile(
        rf"{identifier_boundary('-')}(?<!packages/){re.escape(old)}(?![A-Za-z0-9_-])",
    )
    return pattern.sub(lambda _match: new, text)


def _retarget_distribution(text: str, target: PackageIdentity) -> str:
    if target.import_name == target.distribution_name:
        return text
    lines = text.splitlines(keepends=True)
    section = ""
    output: list[str] = []
    for line in lines:
        header = line.strip()
        if header.startswith("[") and header.endswith("]") and not header.startswith("[["):
            section = header
        updated = line
        if section in _DIST_SECTIONS:
            updated = _retarget_line(line, target.import_name, target.distribution_name)
        output.append(updated)
    return "".join(output)


def _retarget_line(line: str, import_name: str, distribution: str) -> str:
    line = re.sub(
        rf"^{re.escape(import_name)}( = \{{)",
        f"{distribution}\\1",
        line,
    )

    def replace(match: re.Match[str]) -> str:
        updated = _retarget_requirement(match.group(1), import_name, distribution)
        if updated is None:
            return match.group(0)
        return f'"{updated}"'

    return re.sub(r'"([^"]*)"', replace, line)


def _retarget_requirement(value: str, import_name: str, distribution: str) -> str | None:
    parts = split_requirement(value.strip())
    if parts is None:
        return None
    name, rest = parts
    if normalize_distribution(name) != normalize_distribution(import_name):
        return None
    if rest.startswith(" "):
        if not rest.lstrip().startswith(";"):
            return None
    elif rest and rest[0] not in "[<>=!~;":
        return None
    return distribution + rest


def restore_rewrites(changed: list[tuple[Path, str]]) -> None:
    """Write the previous text of each rewritten file."""
    rewrites_desc_by_write_order = reversed(changed)
    for path, text in rewrites_desc_by_write_order:
        write_text(path, text)
