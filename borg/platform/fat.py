import os
import sys
import struct
from ..platformflags import is_win32, is_linux, is_darwin, is_freebsd

# FAT attribute constants - same values across platforms
# See linux/msdos_fs.h, Windows API documentation
FAT_ATTR_READ_ONLY = 0x01
FAT_ATTR_HIDDEN = 0x02
FAT_ATTR_SYSTEM = 0x04
FAT_ATTR_VOLUME_ID = 0x08
FAT_ATTR_DIRECTORY = 0x10
FAT_ATTR_ARCHIVE = 0x20

# Linux-specific ioctl codes for FAT attributes
FAT_IOCTL_GET_ATTRIBUTES = 0x80047210
FAT_IOCTL_SET_ATTRIBUTES = 0x40047211

# FAT filesystem magic numbers for Linux statfs
FAT_MAGIC_NUMBERS = (
    0x4d44,     # MSDOS_SUPER_MAGIC
    0x4006,     # FAT_SUPER_MAGIC
    0x564c,     # VFAT_SUPER_MAGIC
    0x5346544e, # NTFS_SB_MAGIC
    0x58465342, # EXFAT_SUPER_MAGIC
)

# Windows FILE_ATTRIBUTE constants
# Not all are used in FAT, but included for completeness
WIN_FILE_ATTRIBUTE_READONLY = 0x1
WIN_FILE_ATTRIBUTE_HIDDEN = 0x2
WIN_FILE_ATTRIBUTE_SYSTEM = 0x4
WIN_FILE_ATTRIBUTE_DIRECTORY = 0x10
WIN_FILE_ATTRIBUTE_ARCHIVE = 0x20
WIN_FILE_ATTRIBUTE_NORMAL = 0x80

# Mapping between Windows and FAT attributes (identical for basic flags)
WIN_TO_FAT_ATTR_MAP = {
    WIN_FILE_ATTRIBUTE_READONLY: FAT_ATTR_READ_ONLY,
    WIN_FILE_ATTRIBUTE_HIDDEN: FAT_ATTR_HIDDEN,
    WIN_FILE_ATTRIBUTE_SYSTEM: FAT_ATTR_SYSTEM,
    WIN_FILE_ATTRIBUTE_DIRECTORY: FAT_ATTR_DIRECTORY,
    WIN_FILE_ATTRIBUTE_ARCHIVE: FAT_ATTR_ARCHIVE,
}

FAT_TO_WIN_ATTR_MAP = {v: k for k, v in WIN_TO_FAT_ATTR_MAP.items()}


def is_fat_filesystem(path):
    """Detect if the given path is on a FAT filesystem.

    Args:
        path: Path to check

    Returns:
        bool: True if path is on a FAT filesystem, False otherwise
    """
    # Check using statfs on Unix-like systems
    if hasattr(os, 'statfs'):
        try:
            st = os.statfs(path)
            return st.f_type in FAT_MAGIC_NUMBERS
        except Exception:
            return False

    # Windows-specific detection
    elif is_win32:
        try:
            import ctypes
            from ctypes import windll, wintypes

            # Get absolute path and extract drive
            path = os.path.abspath(path)
            drive = os.path.splitdrive(path)[0]
            if not drive:
                return False  # No drive letter, not a filesystem path

            # Add trailing backslash for root directory
            if not drive.endswith('\\'):
                drive += '\\'

            # Prepare buffers for GetVolumeInformation
            fsname = ctypes.create_unicode_buffer(1024)
            volume_name = ctypes.create_unicode_buffer(1024)
            serial_number = wintypes.DWORD(0)
            max_component_length = wintypes.DWORD(0)
            fs_flags = wintypes.DWORD(0)

            # Get filesystem information
            result = windll.kernel32.GetVolumeInformationW(
                drive,
                volume_name, ctypes.sizeof(volume_name),
                ctypes.byref(serial_number),
                ctypes.byref(max_component_length),
                ctypes.byref(fs_flags),
                fsname, ctypes.sizeof(fsname)
            )

            if result == 0:
                return False  # Function failed

            # Check if filesystem is FAT, FAT32, or exFAT
            return fsname.value.upper() in ('FAT', 'FAT32', 'EXFAT')

        except Exception:
            return False

    # Default for unsupported platforms
    return False


def get_fat_attributes(path):
    """Get FAT attributes for a file.

    Args:
        path: Path to the file

    Returns:
        int: FAT attributes as a bitmask

    Raises:
        OSError: If getting attributes fails or is not supported
    """
    # Fast path: check if filesystem is FAT
    if not is_fat_filesystem(path):
        return 0  # Not a FAT filesystem, no attributes

    # Linux implementation using ioctl
    if is_linux:
        import fcntl
        try:
            with open(path, 'rb') as fd:
                attr = fcntl.ioctl(fd, FAT_IOCTL_GET_ATTRIBUTES, "    ")
                return struct.unpack('I', attr)[0]
        except (OSError, IOError):
            # Fall back to stat-based attributes if ioctl fails
            pass

    # Windows implementation
    elif is_win32:
        try:
            import ctypes
            from ctypes import windll, wintypes

            # Convert path to Unicode for Windows API
            u_path = os.path.abspath(path)

            # Get file attributes
            attr = windll.kernel32.GetFileAttributesW(u_path)
            if attr == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                return 0

            # Convert Windows attributes to FAT attributes
            fat_attr = 0
            for win_attr, fat_flag in WIN_TO_FAT_ATTR_MAP.items():
                if attr & win_attr:
                    fat_attr |= fat_flag

            return fat_attr

        except Exception:
            return 0

    # Fallback for other platforms or if previous methods failed
    # Use stat-based heuristics to determine basic attributes
    try:
        stat_info = os.stat(path)
        fat_attr = 0

        # Directory attribute
        if os.path.isdir(path):
            fat_attr |= FAT_ATTR_DIRECTORY

        # Read-only attribute (not writable by user)
        if not os.access(path, os.W_OK):
            fat_attr |= FAT_ATTR_READ_ONLY

        # Archive attribute (always set for non-directories)
        if not os.path.isdir(path):
            fat_attr |= FAT_ATTR_ARCHIVE

        return fat_attr

    except (OSError, IOError):
        return 0


def set_fat_attributes(path, attr):
    """Set FAT attributes for a file.

    Args:
        path: Path to the file
        attr: FAT attributes as a bitmask

    Raises:
        OSError: If setting attributes fails or is not supported
    """
    # Fast path: check if filesystem is FAT
    if not is_fat_filesystem(path):
        return  # Not a FAT filesystem, nothing to do

    # Linux implementation using ioctl
    if is_linux:
        import fcntl
        try:
            with open(path, 'rb+') as fd:
                buf = struct.pack('I', attr)
                fcntl.ioctl(fd, FAT_IOCTL_SET_ATTRIBUTES, buf)
                return
        except (OSError, IOError):
            # Fall back to chmod if ioctl fails
            pass

    # Windows implementation
    elif is_win32:
        try:
            import ctypes
            from ctypes import windll, wintypes

            # Convert path to Unicode for Windows API
            u_path = os.path.abspath(path)

            # Get current attributes first
            current_attr = windll.kernel32.GetFileAttributesW(u_path)
            if current_attr == 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                raise OSError(f"Failed to get attributes for {path}")

            # Convert FAT attributes to Windows attributes
            new_attr = current_attr

            # Clear existing attributes that we're managing
            for win_flag in WIN_TO_FAT_ATTR_MAP.keys():
                new_attr &= ~win_flag

            # Set new attributes
            for fat_flag, win_flag in FAT_TO_WIN_ATTR_MAP.items():
                if attr & fat_flag:
                    new_attr |= win_flag

            # Set file attributes
            if not windll.kernel32.SetFileAttributesW(u_path, new_attr):
                raise OSError(f"Failed to set attributes for {path}")

            return

        except Exception as e:
            raise OSError(f"Failed to set FAT attributes: {e}")

    # Fallback for other platforms or if previous methods failed
    # Set permissions based on read-only attribute
    try:
        if attr & FAT_ATTR_READ_ONLY:
            # Make file read-only
            current_mode = os.stat(path).st_mode
            os.chmod(path, current_mode & ~0o222)  # Remove write permission
        else:
            # Make file writable
            current_mode = os.stat(path).st_mode
            os.chmod(path, current_mode | 0o200)  # Add user write permission
    except (OSError, IOError) as e:
        raise OSError(f"Failed to set FAT attributes: {e}")
