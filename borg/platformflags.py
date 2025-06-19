# Platform detection flags

import sys
import os

# Operating system detection
is_win32 = sys.platform == 'win32'
is_linux = sys.platform.startswith('linux')
is_darwin = sys.platform == 'darwin'
is_freebsd = sys.platform.startswith('freebsd')
is_cygwin = sys.platform.startswith('cygwin')
