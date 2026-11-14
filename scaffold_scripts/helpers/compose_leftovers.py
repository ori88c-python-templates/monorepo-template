"""Report ``compose.yaml`` lines that still name a deleted app.

The scaffold commands never write ``compose.yaml``. After a delete, the
service for that app is the agent's job, described in the scaffold skill.
This module only finds the lines so the success output can point at them.
"""

import re

from helpers.names import AppIdentity, identifier_boundary


def compose_leftover_lines(text: str, identity: AppIdentity) -> list[int]:
    """Return the 1-based line numbers in ``text`` that still reference ``identity``.

    A line counts when it names the app's Dockerfile path, an env variable
    with the app's prefix, or the distribution name as a service key or a
    whole token (``depends_on`` entries, image names, profile names).

    Args:
        text: The current ``compose.yaml``.
        identity: The app that was just deleted.

    Returns:
        Sorted line numbers. Empty when Compose no longer mentions the app.
    """
    dockerfile = re.compile(rf"apps/{re.escape(identity.name)}/Dockerfile")
    prefix = re.compile(rf"{identifier_boundary()}{re.escape(identity.env_prefix)}__")
    distribution = re.compile(
        rf"{identifier_boundary('-')}{re.escape(identity.distribution_name)}(?![A-Za-z0-9_-])",
    )
    found: list[int] = []
    compose_lines = text.splitlines()
    for number, line in enumerate(compose_lines, start=1):
        if dockerfile.search(line) or prefix.search(line) or distribution.search(line):
            found.append(number)
    return found


def leftover_report(identity: AppIdentity, lines: list[int]) -> str:
    """Return the second success line that names the leftover Compose lines.

    Args:
        identity: The deleted app.
        lines: Output of :func:`compose_leftover_lines`. Must not be empty.

    Returns:
        One sentence with the line numbers and where the procedure lives.
    """
    listed = ", ".join(str(number) for number in lines)
    return (
        f"compose.yaml still references '{identity.name}' on lines {listed}. "
        "Remove the service as the scaffold skill describes."
    )
