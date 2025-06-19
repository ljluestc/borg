"""
Flags for Platform-specific APIs.

Use these Flags instead of sys.platform.startswith('<OS>') or try/except.
"""

import sys

is_win32 = sys.platform.startswith("win32")
is_cygwin = sys.platform.startswith("cygwin")

is_linux = sys.platform.startswith("linux")
is_freebsd = sys.platform.startswith("freebsd")
is_darwin = sys.platform.startswith("darwin")

# Map invalid Windows characters to Unicode remap range (above 0xF000)
# Based on CIFS specification for Windows file systems
# Characters: *?<>|: (backslash is not remapped)
mapchars = {ord('*'): 0xF000, ord('?'): 0xF001, ord('<'): 0xF002,
           ord('>'): 0xF003, ord('|'): 0xF004, ord(':'): 0xF005} if is_win32 else {}
