import os
import unicodedata

from ..platformflags import is_win32, mapchars


def safe_path(path):
    """
    Convert file path to handle platform-specific constraints.
    On Windows, this maps invalid characters to the Unicode remap range.

    :param path: Original file path
    :return: Path with platform-specific handling applied
    """
    if not is_win32:
        return path

    return path.translate(mapchars)


def original_path(path):
    """
    Convert remapped file path back to its original form.
    On Windows, this maps characters from the Unicode remap range back to their original form.

    :param path: Path with remapped characters
    :return: Original file path
    """
    if not is_win32:
        return path

    # Create reverse mapping
    reverse_mapchars = {v: k for k, v in mapchars.items()}
    return path.translate(reverse_mapchars)
