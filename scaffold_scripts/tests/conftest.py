"""Put the scaffold commands on the import path."""

import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent
for directory in (SCRIPTS, TESTS):
    entry = str(directory)
    if entry not in sys.path:
        sys.path.insert(0, entry)
