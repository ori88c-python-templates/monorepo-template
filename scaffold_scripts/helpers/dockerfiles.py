"""Dockerfile edits that stay the same for every app image."""

import re
from typing import Final

_APP_COPIES: Final = re.compile(r"(?m)^COPY apps/\S+ \./apps/\S+\n(?:COPY apps/\S+ \./apps/\S+\n)*")
_PACKAGE: Final = re.compile(r"--package \S+")
_COMMAND: Final = re.compile(r'CMD \["[^"]+"\]')


def use_apps_copy(text: str) -> str:
    """Copy the whole ``apps`` directory in one instruction.

    A per-app ``COPY`` list has to change every time an app is added.
    ``COPY apps ./apps`` does not. A file that already uses that line is
    returned unchanged.
    """
    return _APP_COPIES.sub("COPY apps ./apps\n", text, count=1)


def set_image_command(text: str, distribution_name: str) -> str:
    """Point the image install and the container command at ``distribution_name``."""
    text = _PACKAGE.sub(f"--package {distribution_name}", text, count=1)
    return _COMMAND.sub(f'CMD ["{distribution_name}"]', text, count=1)


def set_published_port(text: str, old: int, new: int) -> str:
    """Replace ``EXPOSE`` and the healthcheck host port.

    Other numbers in the file, including dependency pins, stay as they are.
    """
    if old == new:
        return text
    old_text = str(old)
    new_text = str(new)

    def one_line(line: str) -> str:
        if line.startswith("EXPOSE ") or "127.0.0.1:" in line:
            return line.replace(old_text, new_text)
        return line

    return "".join(one_line(line) for line in text.splitlines(keepends=True))
