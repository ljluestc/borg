import os
from unittest import mock
import pytest
from _pytest import monkeypatch

from borg.platform import fat
from borg.platform.fat_attributes import FATAttributes
from borg.platformflags import is_win32, is_linux, is_darwin, is_freebsd


@pytest.fixture
def mock_fat_functions(monkeypatch):
    """Mock FAT filesystem functions for testing."""
    # Mock is_fat_filesystem to always return True
    monkeypatch.setattr(fat, "is_fat_filesystem", lambda path: True)

    # Start with empty attributes
    current_attrs = [0]

    # Mock get_fat_attributes
    def mock_get_attrs(path):
        return current_attrs[0]

    # Mock set_fat_attributes
    def mock_set_attrs(path, attrs):
        current_attrs[0] = attrs

    monkeypatch.setattr(fat, "get_fat_attributes", mock_get_attrs)
    monkeypatch.setattr(fat, "set_fat_attributes", mock_set_attrs)

    return current_attrs


class TestFATAttributes:
    """Tests for the FATAttributes helper class."""

    def test_init_empty(self):
        """Test creating an empty instance."""
        attrs = FATAttributes()
        assert attrs.get_attributes() == 0

    def test_init_with_attributes(self):
        """Test creating with raw attribute flags."""
        flags = FATAttributes.READ_ONLY | FATAttributes.ARCHIVE
        attrs = FATAttributes(attributes=flags)
        assert attrs.get_attributes() == flags
        assert attrs.is_read_only() is True
        assert attrs.is_archive() is True

    def test_init_with_path(self, mock_fat_functions):
        """Test creating from a file path."""
        # Set mock attributes
        mock_fat_functions[0] = FATAttributes.HIDDEN | FATAttributes.SYSTEM

        # Create instance
        attrs = FATAttributes(path="/fake/path")

        # Verify flags
        assert attrs.is_hidden() is True
        assert attrs.is_system() is True
        assert attrs.is_read_only() is False

    def test_flag_methods(self):
        """Test setting and checking individual flags."""
        attrs = FATAttributes()
        # Initially all flags should be off
        assert attrs.is_read_only() is False
        assert attrs.is_hidden() is False
        assert attrs.is_system() is False
        assert attrs.is_volume_id() is False
        assert attrs.is_directory() is False
        assert attrs.is_archive() is False

        # Set individual flags
        attrs.set_read_only()
        assert attrs.is_read_only() is True

        attrs.set_hidden()
        assert attrs.is_hidden() is True

        attrs.set_system()
        assert attrs.is_system() is True

        attrs.set_archive()
        assert attrs.is_archive() is True

        # Clear a flag
        attrs.set_read_only(False)
        assert attrs.is_read_only() is False
        assert attrs.is_hidden() is True  # Others remain unchanged

    def test_get_set_attributes(self):
        """Test getting and setting raw attribute flags."""
        attrs = FATAttributes()

        # Set flags
        flags = FATAttributes.READ_ONLY | FATAttributes.ARCHIVE
        attrs.set_attributes(flags)

        # Check result
        assert attrs.get_attributes() == flags
        assert attrs.is_read_only() is True
        assert attrs.is_archive() is True

    def test_apply(self, mock_fat_functions):
        """Test applying attributes to a file."""
        # Set up attributes
        flags = FATAttributes.READ_ONLY | FATAttributes.HIDDEN
        attrs = FATAttributes(attributes=flags)

        # Apply to file
        attrs.apply("/fake/path")

        # Check that attributes were set
        assert mock_fat_functions[0] == flags

    def test_class_methods(self, mock_fat_functions):
        """Test class methods for getting and setting attributes."""
        # Set mock attributes
        mock_fat_functions[0] = FATAttributes.ARCHIVE

        # Test get() class method
        attrs = FATAttributes.get("/fake/path")
        assert attrs.is_archive() is True

        # Test set() class method
        flags = FATAttributes.READ_ONLY | FATAttributes.SYSTEM
        FATAttributes.set("/fake/path", flags)
        assert mock_fat_functions[0] == flags

    def test_is_fat_filesystem(self, monkeypatch):
        """Test checking if a path is on a FAT filesystem."""
        # Mock fat.is_fat_filesystem
        mock_results = {}
        def mock_is_fat(path):
            return path in mock_results and mock_results[path]

        monkeypatch.setattr(fat, "is_fat_filesystem", mock_is_fat)

        # Set up test paths
        mock_results["/fat/path"] = True
        mock_results["/non-fat/path"] = False

        # Test
        assert FATAttributes.is_fat_filesystem("/fat/path") is True
        assert FATAttributes.is_fat_filesystem("/non-fat/path") is False
        assert FATAttributes.is_fat_filesystem("/unknown/path") is False

    def test_representation(self):
        """Test string representation of attributes."""
        # Empty attributes
        attrs = FATAttributes()
        assert "NONE" in repr(attrs)

        # Single attribute
        attrs = FATAttributes(attributes=FATAttributes.READ_ONLY)
        assert "READ_ONLY" in repr(attrs)

        # Multiple attributes
        attrs = FATAttributes(attributes=FATAttributes.HIDDEN | FATAttributes.ARCHIVE)
        assert "HIDDEN" in repr(attrs)
        assert "ARCHIVE" in repr(attrs)

    def test_non_fat_filesystem(self, monkeypatch):
        """Test behavior when path is not on a FAT filesystem."""
        # Mock is_fat_filesystem to return False
        monkeypatch.setattr(fat, "is_fat_filesystem", lambda path: False)

        path = "/non-fat/path"
        attrs = FATAttributes.get(path)
        assert attrs.get_attributes() == 0

    def test_non_fat_initial_attributes(self, monkeypatch):
        """Test that initial attributes are empty on non-FAT filesystems."""
        # Mock is_fat_filesystem to return False
        monkeypatch.setattr(fat, "is_fat_filesystem", lambda path: False)

        attrs = FATAttributes(path="/non-fat/path")
        assert attrs.get_attributes() == 0
        assert attrs.is_read_only() is False
        assert attrs.is_hidden() is False
        assert attrs.is_system() is False

    def test_non_fat_attribute_changes(self, monkeypatch):
        """Test that attribute changes are no-op on non-FAT filesystems."""
        # Mock is_fat_filesystem to return False
        monkeypatch.setattr(fat, "is_fat_filesystem", lambda path: False)

        attrs = FATAttributes()
        attrs.set_read_only(True)
        attrs.set_hidden(True)
        # Should not raise exceptions but have no effect
        attrs.apply("/non-fat/path")
        # Verify attributes were not changed
        new_attrs = FATAttributes.get("/non-fat/path")
        assert new_attrs.get_attributes() == 0
