from . import fat


class FATAttributes:
    """Class for manipulating FAT file attributes.

    This class provides a high-level interface for working with FAT attributes
    that's consistent across platforms.
    """

    # Attribute constants
    READ_ONLY = fat.FAT_ATTR_READ_ONLY
    HIDDEN = fat.FAT_ATTR_HIDDEN
    SYSTEM = fat.FAT_ATTR_SYSTEM
    VOLUME_ID = fat.FAT_ATTR_VOLUME_ID
    DIRECTORY = fat.FAT_ATTR_DIRECTORY
    ARCHIVE = fat.FAT_ATTR_ARCHIVE

    # Attribute names for display/debugging
    ATTRIBUTE_NAMES = {
        READ_ONLY: "READ_ONLY",
        HIDDEN: "HIDDEN",
        SYSTEM: "SYSTEM",
        VOLUME_ID: "VOLUME_ID",
        DIRECTORY: "DIRECTORY",
        ARCHIVE: "ARCHIVE"
    }

    def __init__(self, path=None, attributes=None):
        """Initialize with either a path or attribute flags.

        Args:
            path: Path to file to get attributes from
            attributes: Raw attribute flags (integer bitmask)
        """
        self._attrs = 0

        if path is not None:
            self._attrs = fat.get_fat_attributes(path)
        elif attributes is not None:
            self._attrs = attributes

    def __repr__(self):
        attr_names = []
        for flag, name in self.ATTRIBUTE_NAMES.items():
            if self._attrs & flag:
                attr_names.append(name)

        if not attr_names:
            attr_names = ["NONE"]

        return f"FATAttributes({' | '.join(attr_names)})"

    def is_read_only(self):
        """Check if the READ_ONLY flag is set."""
        return bool(self._attrs & self.READ_ONLY)

    def is_hidden(self):
        """Check if the HIDDEN flag is set."""
        return bool(self._attrs & self.HIDDEN)

    def is_system(self):
        """Check if the SYSTEM flag is set."""
        return bool(self._attrs & self.SYSTEM)

    def is_volume_id(self):
        """Check if the VOLUME_ID flag is set."""
        return bool(self._attrs & self.VOLUME_ID)

    def is_directory(self):
        """Check if the DIRECTORY flag is set."""
        return bool(self._attrs & self.DIRECTORY)

    def is_archive(self):
        """Check if the ARCHIVE flag is set."""
        return bool(self._attrs & self.ARCHIVE)

    def set_read_only(self, value=True):
        """Set or clear the READ_ONLY flag."""
        if value:
            self._attrs |= self.READ_ONLY
        else:
            self._attrs &= ~self.READ_ONLY
        return self

    def set_hidden(self, value=True):
        """Set or clear the HIDDEN flag."""
        if value:
            self._attrs |= self.HIDDEN
        else:
            self._attrs &= ~self.HIDDEN
        return self

    def set_system(self, value=True):
        """Set or clear the SYSTEM flag."""
        if value:
            self._attrs |= self.SYSTEM
        else:
            self._attrs &= ~self.SYSTEM
        return self

    def set_archive(self, value=True):
        """Set or clear the ARCHIVE flag."""
        if value:
            self._attrs |= self.ARCHIVE
        else:
            self._attrs &= ~self.ARCHIVE
        return self

    def get_attributes(self):
        """Get the raw attribute bitmask."""
        return self._attrs

    def set_attributes(self, attributes):
        """Set the raw attribute bitmask."""
        self._attrs = attributes
        return self

    def apply(self, path):
        """Apply the attributes to a file."""
        fat.set_fat_attributes(path, self._attrs)
        return self

    @classmethod
    def get(cls, path):
        """Get attributes for a file and return a FATAttributes instance."""
        return cls(path=path)

    @classmethod
    def set(cls, path, attributes):
        """Set attributes for a file from raw attribute flags."""
        fat.set_fat_attributes(path, attributes)

    @classmethod
    def is_fat_filesystem(cls, path):
        """Check if a path is on a FAT filesystem."""
        return fat.is_fat_filesystem(path)
