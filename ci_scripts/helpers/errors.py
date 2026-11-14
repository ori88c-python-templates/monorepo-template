"""Failures that stop affected-test selection."""


class SelectionError(Exception):
    """The affected set cannot be decided.

    The message is the whole report. The CLI prints it and exits.
    """
