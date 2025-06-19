INVALID_CHARS = {'*', '?', '<', '>', '|', ':'}
OFFSET = 0xF000
import sys

# Map invalid Windows characters to Unicode remap range (above 0xF000)
# Based on CIFS specification for Windows file systems
# Characters: *?<>|: (backslash is not remapped)
INVALID_CHARS = {'*', '?', '<', '>', '|', ':'}
OFFSET = 0xF000

# Check if we're running on Windows
is_win32 = sys.platform.startswith("win32")

# Create mapping dictionary
char_map = {ord(ch): OFFSET + ord(ch) for ch in INVALID_CHARS} if is_win32 else {}


def map_invalid_chars(path: str) -> str:
    """
    Map invalid Win32 filename characters to a private use area above 0xF000.

    :param path: Original file path with potentially invalid characters
    :return: Path with invalid characters mapped to safe Unicode range
    """
    if not is_win32:
        return path

    # Translate using the mapping dictionary
    return path.translate(char_map)


def unmap_chars(path: str) -> str:
    """
    Convert remapped file path back to its original form.

    :param path: Path with remapped characters
    :return: Original file path
    """
    if not is_win32:
        return path

    # Create reverse mapping
    reverse_map = {v: k for k, v in char_map.items()}
    return path.translate(reverse_map)
def map_invalid_chars(path: str) -> str:
    """Map invalid Win32 filename characters to a private use area above 0xF000."""
    # ...existing code...
    new_chars = []
    for ch in path:
        if ch in INVALID_CHARS:
            new_chars.append(chr(OFFSET + ord(ch)))
        else:
            new_chars.append(ch)
    return ''.join(new_chars)
