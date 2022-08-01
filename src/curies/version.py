# -*- coding: utf-8 -*-

"""Version information for :mod:`curies`."""

__all__ = [
    "VERSION",
    "get_version",
]

VERSION = "0.1.1-dev"


def get_version():
    """Get the :mod:`curies` version string, including a git hash."""
    return VERSION
