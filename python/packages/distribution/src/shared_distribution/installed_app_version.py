"""The installed distribution that provides an application import."""

import importlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from importlib.metadata import PackageNotFoundError, distributions, packages_distributions, version
from os import PathLike
from pathlib import Path
from typing import Protocol


class PthDistribution(Protocol):
    """Enough of ``importlib.metadata.Distribution`` to recognise an editable ``.pth``."""

    @property
    def version(self) -> str:
        """The distribution version string."""
        ...

    @property
    def files(self) -> Sequence[str | PathLike[str]] | None:
        """Paths recorded on the distribution, or ``None`` if unknown."""
        ...

    def locate_file(self, path: str | PathLike[str]) -> object:
        """Resolve ``path`` to a filesystem location.

        Args:
            path: A path recorded on the distribution, typically a ``.pth`` name.

        Returns:
            The filesystem location of ``path``.
        """
        ...


def pth_points_at_src(dist: PthDistribution, src_dir: Path) -> bool:
    """Return True when ``dist`` has a ``.pth`` whose contents resolve to ``src_dir``.

    Editable ``uv`` installs list the ``.pth`` in ``RECORD`` but keep the file in
    ``site-packages``, so the text is read via ``locate_file``, not
    ``Distribution.read_text``.

    Args:
        dist: An installed distribution or a test double with the same surface.
        src_dir: The ``src/`` directory of the application checkout.

    Returns:
        True when a ``.pth`` line names ``src_dir``.
    """
    for file in dist.files or ():
        if not str(file).endswith(".pth"):
            continue
        pth_path = Path(str(dist.locate_file(file)))
        try:
            text = pth_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if Path(stripped).resolve() == src_dir:
                return True
    return False


def installed_app_version(
    import_name: str,
    *,
    dist_names_by_import: Mapping[str, list[str]] | None = None,
    version_for: Callable[[str], str] | None = None,
    dists: Iterable[PthDistribution] | None = None,
    src_dir: Path | None = None,
) -> str:
    """Read the installed distribution version that provides ``import_name``.

    Wheel installs map the import via ``packages_distributions``. Editable ``uv``
    installs only record a ``.pth`` pointing at ``src/``. Metadata comes from the
    installed dist (populated from ``pyproject.toml`` at install), not from
    parsing the toml file at runtime.

    Optional keyword arguments are for tests: they inject a catalog instead of
    patching ``importlib.metadata``. Production callers pass ``import_name`` only.

    Args:
        import_name: Top-level application import, such as ``billing_api``.
        dist_names_by_import: ``packages_distributions()`` result, distribution
            names keyed by import name. ``None`` reads the real catalog. An empty
            mapping skips the wheel branch.
        version_for: ``importlib.metadata.version``. ``None`` uses the real
            function.
        dists: Distributions to scan for an editable ``.pth``. ``None`` uses
            ``importlib.metadata.distributions()``.
        src_dir: Directory a matching ``.pth`` must name. ``None`` uses the
            parent of the imported package, which is ``src/`` in this layout.

    Returns:
        The version string of the distribution that exports ``import_name``.

    Raises:
        PackageNotFoundError: If no installed distribution provides the import.
    """
    if dist_names_by_import is None:
        dist_names_by_import = packages_distributions()
    dist_names = dist_names_by_import.get(import_name)
    if dist_names:
        lookup = version if version_for is None else version_for
        return lookup(dist_names[0])

    resolved_src = _default_src_dir(import_name) if src_dir is None else src_dir
    catalog = distributions() if dists is None else dists
    for dist in catalog:
        if pth_points_at_src(dist, resolved_src):
            return dist.version
    raise PackageNotFoundError(import_name)


def _default_src_dir(import_name: str) -> Path:
    """Return the ``src/`` directory that contains ``import_name``.

    Args:
        import_name: Top-level application import.

    Returns:
        The parent of the imported package directory.

    Raises:
        PackageNotFoundError: If the import cannot be loaded.
    """
    try:
        module = importlib.import_module(import_name)
    except ModuleNotFoundError as exc:
        raise PackageNotFoundError(import_name) from exc
    module_file = module.__file__
    if module_file is None:
        raise PackageNotFoundError(import_name)
    return Path(module_file).resolve().parent.parent
