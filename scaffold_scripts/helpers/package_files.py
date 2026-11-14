"""Write the empty src-layout tree for a new package."""

from pathlib import Path

from helpers.package_names import PackageIdentity
from helpers.paths import write_text


def write_package_skeleton(directory: Path, identity: PackageIdentity) -> None:
    """Create ``directory`` with an importable module and one test.

    ``tests/`` and ``tests/<import>/`` have no ``__init__.py``. The package
    has no dependencies, Alembic tree, or pytest plugin.
    """
    source = directory / "src" / identity.import_name
    tests = directory / "tests" / identity.import_name
    source.mkdir(parents=True)
    tests.mkdir(parents=True)
    write_text(directory / "pyproject.toml", _pyproject(identity))
    write_text(directory / "README.md", f"{identity.import_name} package.\n")
    write_text(source / "__init__.py", f'"""{identity.import_name} package."""\n')
    write_text(source / "py.typed", "")
    write_text(tests / "test_import.py", _import_test(identity.import_name))


def _pyproject(identity: PackageIdentity) -> str:
    return (
        "[project]\n"
        f'name = "{identity.distribution_name}"\n'
        'version = "1.0.0"\n'
        f'description = "{identity.import_name} package."\n'
        'readme = "README.md"\n'
        'requires-python = ">=3.14,<3.15"\n'
        'license = "MIT"\n'
        "\n"
        "[build-system]\n"
        'requires = ["uv_build>=0.12.9,<0.14"]\n'
        'build-backend = "uv_build"\n'
        "\n"
        "[tool.uv.build-backend]\n"
        f'module-name = "{identity.import_name}"\n'
    )


def _import_test(import_name: str) -> str:
    return (
        '"""Import the package."""\n'
        "\n"
        f"import {import_name}\n"
        "\n"
        "\n"
        "def test_import() -> None:\n"
        '    """The module name is the installed package."""\n'
        f'    assert {import_name}.__name__ == "{import_name}"\n'
    )
