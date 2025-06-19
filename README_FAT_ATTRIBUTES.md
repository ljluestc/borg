# FAT Attributes Support in Borg

## Overview

Borg now supports preserving and restoring FAT filesystem attributes on both Linux and Windows platforms. This is important for backup integrity when working with FAT-formatted drives such as USB flash drives, SD cards, and EFI system partitions.

## FAT Attributes

FAT filesystems support the following attributes:

- **READ_ONLY**: File cannot be modified
- **HIDDEN**: File is hidden from normal directory listings
- **SYSTEM**: File is used by the operating system
- **VOLUME_ID**: Volume label or identifier
- **DIRECTORY**: Entry is a directory
- **ARCHIVE**: File has been modified since last backup

## Implementation

The implementation works across platforms:

### Linux

On Linux, we use the kernel's FAT-specific ioctls (`FAT_IOCTL_GET_ATTRIBUTES` and `FAT_IOCTL_SET_ATTRIBUTES`) to directly read and write the on-disk FAT attribute bytes.

### Windows

On Windows, we use the Win32 API functions `GetFileAttributesW` and `SetFileAttributesW` to access and modify file attributes. The Windows file attribute constants map directly to the FAT attributes.

### Other Platforms

On other platforms, we use a best-effort approach based on file permissions and type.

## Performance Optimization

For better performance, the code includes fast detection of FAT filesystems:

- On Linux, we use `statfs()` to check the filesystem type magic number
- On Windows, we use `GetVolumeInformationW()` to query the filesystem type

If a file is not on a FAT filesystem, attribute operations become no-ops, avoiding unnecessary work.

## Usage

### Low-level API

```python
from borg.platform import fat

# Check if path is on a FAT filesystem
is_fat = fat.is_fat_filesystem("/path/to/file")

# Get attributes
attr = fat.get_fat_attributes("/path/to/file")
if attr & fat.FAT_ATTR_READ_ONLY:
    print("File is read-only")

# Set attributes
fat.set_fat_attributes("/path/to/file", fat.FAT_ATTR_HIDDEN | fat.FAT_ATTR_SYSTEM)
```

### High-level API

```python
from borg.platform.fat_attributes import FATAttributes

# Get attributes
attrs = FATAttributes.get("/path/to/file")
if attrs.is_read_only():
    print("File is read-only")

# Set attributes
attrs.set_hidden().set_system().apply("/path/to/file")

# Create attributes from scratch
attrs = FATAttributes()
attrs.set_read_only().set_archive().apply("/path/to/file")
```

## Testing

Comprehensive tests are provided for both the low-level API in `tests/platform/test_fat.py` and the high-level API in `tests/platform/test_fat_attributes.py`.
