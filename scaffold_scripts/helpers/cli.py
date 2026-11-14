"""Exit path shared by the scaffold commands."""

import sys
from typing import NoReturn

from helpers.errors import ScaffoldError


def succeed(message: str) -> None:
    """Write the success report. Delete may add a second line about Compose."""
    sys.stdout.write(f"{message}\n")


def fail(error: ScaffoldError) -> NoReturn:
    """Write the one-line error and exit."""
    sys.stderr.write(f"{error}\n")
    raise SystemExit(1)
