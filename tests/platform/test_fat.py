import pytest
import os
import sys
import struct
import fcntl
from unittest import mock
from borg.platform import fat
from borg.platformflags import is_win32, is_linux, is_darwin, is_freebsd


def test_is_fat_filesystem(monkeypatch):
    # Skip the test if running on a platform that doesn't support the approach we're testing
    if is_win32:
        # Test Windows implementation
        with mock.patch('ctypes.windll.kernel32.GetVolumeInformationW') as mock_get_vol_info:
            # Setup mock for FAT filesystem
            def side_effect_fat(drive, vol_name, vol_name_size, serial_num, max_len, flags, fs_name, fs_name_size):
                # Write "FAT32" to the fs_name buffer
                fs_name.value = "FAT32"
                return 1  # Success

            mock_get_vol_info.side_effect = side_effect_fat
            assert fat.is_fat_filesystem("C:\\some\\path")

            # Setup mock for NTFS filesystem
            def side_effect_ntfs(drive, vol_name, vol_name_size, serial_num, max_len, flags, fs_name, fs_name_size):
                fs_name.value = "NTFS"
                return 1  # Success

            mock_get_vol_info.side_effect = side_effect_ntfs
            assert not fat.is_fat_filesystem("C:\\some\\path")

            # Test exception handling
            mock_get_vol_info.side_effect = Exception("Test exception")
            assert not fat.is_fat_filesystem("C:\\some\\path")

    elif hasattr(os, 'statfs'):
        # Test Unix implementation
        class statfs_result:
            def __init__(self, f_type):
                self.f_type = f_type

        # Mock statfs for FAT filesystem
        monkeypatch.setattr(os, "statfs", lambda path: statfs_result(0x4d44))  # MSDOS_SUPER_MAGIC
        assert fat.is_fat_filesystem("/fake/fat")

        # Mock statfs for VFAT filesystem
        monkeypatch.setattr(os, "statfs", lambda path: statfs_result(0x564c))  # VFAT_SUPER_MAGIC
        assert fat.is_fat_filesystem("/fake/vfat")

        # Mock statfs for non-FAT filesystem
        monkeypatch.setattr(os, "statfs", lambda path: statfs_result(0x1234))  # Some other filesystem
        assert not fat.is_fat_filesystem("/fake/notfat")

        # Test exception handling
        def raises_exception(path):
            raise OSError("Test exception")
        monkeypatch.setattr(os, "statfs", raises_exception)
        assert not fat.is_fat_filesystem("/fake/error")

    else:
        pytest.skip("No FAT filesystem detection mechanism available on this platform")


@pytest.fixture
def mock_is_fat_filesystem(monkeypatch):
    """Mock is_fat_filesystem to always return True for testing."""
    monkeypatch.setattr(fat, "is_fat_filesystem", lambda path: True)


    @pytest.fixture
    def mock_is_fat_filesystem(monkeypatch):
        """Mock is_fat_filesystem to always return True for testing."""
        monkeypatch.setattr(fat, "is_fat_filesystem", lambda path: True)


def test_fat_attributes_linux(monkeypatch, mock_is_fat_filesystem):
    """Test FAT attributes on Linux using ioctl."""
    if not is_linux:
        pytest.skip("Linux-specific test")

    called = {}

    class FakeFD:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def fileno(self): return 42

    def fake_open(path, mode):
        return FakeFD()

    def fake_ioctl(fd, op, buf):
        called['op'] = op
        if op == fat.FAT_IOCTL_GET_ATTRIBUTES:
            # Return ARCHIVE | READ_ONLY (0x21)
            return b'\x21\x00\x00\x00'
        elif op == fat.FAT_IOCTL_SET_ATTRIBUTES:
            called['set'] = buf
            return 0

    # Patch functions
    monkeypatch.setattr("builtins.open", fake_open)
    import fcntl
    monkeypatch.setattr(fcntl, "ioctl", fake_ioctl)

    # Test getting attributes
    attr = fat.get_fat_attributes("/fake/file")
    assert attr == 0x21  # ARCHIVE | READ_ONLY
    assert called['op'] == fat.FAT_IOCTL_GET_ATTRIBUTES

    # Test setting attributes
    new_attr = fat.FAT_ATTR_HIDDEN | fat.FAT_ATTR_READ_ONLY  # 0x03
    fat.set_fat_attributes("/fake/file", new_attr)
    assert called['set'] == struct.pack('I', new_attr)
    assert called['op'] == fat.FAT_IOCTL_SET_ATTRIBUTES


def test_fat_attributes_windows(monkeypatch, mock_is_fat_filesystem):
    """Test FAT attributes on Windows."""
    if not is_win32:
        pytest.skip("Windows-specific test")

    # Mock Windows API functions
    with mock.patch('ctypes.windll.kernel32.GetFileAttributesW') as mock_get_attr, \
         mock.patch('ctypes.windll.kernel32.SetFileAttributesW') as mock_set_attr:

        # Setup mock for getting attributes
        # Return READ_ONLY | ARCHIVE (0x21)
        mock_get_attr.return_value = fat.WIN_FILE_ATTRIBUTE_READONLY | fat.WIN_FILE_ATTRIBUTE_ARCHIVE

        # Setup mock for setting attributes
        mock_set_attr.return_value = 1  # Success

        # Test getting attributes
        attr = fat.get_fat_attributes("C:\\fake\\file.txt")
        assert attr == fat.FAT_ATTR_READ_ONLY | fat.FAT_ATTR_ARCHIVE  # 0x21
        mock_get_attr.assert_called_once()

        # Test setting attributes (HIDDEN | READ_ONLY = 0x03)
        new_attr = fat.FAT_ATTR_HIDDEN | fat.FAT_ATTR_READ_ONLY
        fat.set_fat_attributes("C:\\fake\\file.txt", new_attr)
        mock_set_attr.assert_called_once()

        # Test error handling
        mock_get_attr.reset_mock()
        mock_set_attr.reset_mock()

        # INVALID_FILE_ATTRIBUTES
        mock_get_attr.return_value = 0xFFFFFFFF
        attr = fat.get_fat_attributes("C:\\fake\\nonexistent.txt")
        assert attr == 0

        # Test exception during SetFileAttributesW
        mock_get_attr.return_value = 0x20  # ARCHIVE
        mock_set_attr.return_value = 0  # Failure
        with pytest.raises(OSError):
            fat.set_fat_attributes("C:\\fake\\readonly.txt", 0x01)


def test_fat_attributes_fallback(monkeypatch, mock_is_fat_filesystem):
    """Test fallback methods for FAT attributes on all platforms."""
    # Mock native methods to fail
    if is_linux:
        import fcntl
        def fake_ioctl_fail(*args, **kwargs):
            raise OSError("ioctl not supported")
        monkeypatch.setattr(fcntl, "ioctl", fake_ioctl_fail)

    if is_win32:
        with mock.patch('ctypes.windll.kernel32.GetFileAttributesW', return_value=0xFFFFFFFF), \
             mock.patch('ctypes.windll.kernel32.SetFileAttributesW', return_value=0):

            # Mock stat and access functions
            with mock.patch('os.stat') as mock_stat, \
                 mock.patch('os.path.isdir') as mock_isdir, \
                 mock.patch('os.access') as mock_access, \
                 mock.patch('os.chmod') as mock_chmod:

                # Setup for a regular file with read-only attribute
                mock_stat.return_value.st_mode = 0o444  # read-only
                mock_isdir.return_value = False
                mock_access.return_value = False  # Not writable

                # Test getting attributes using fallback
                attr = fat.get_fat_attributes("/fake/file")
                assert attr & fat.FAT_ATTR_READ_ONLY
                assert attr & fat.FAT_ATTR_ARCHIVE
                assert not (attr & fat.FAT_ATTR_DIRECTORY)

                # Setup for directory
                mock_isdir.return_value = True
                mock_access.return_value = True  # Writable

                # Test getting attributes for directory
                attr = fat.get_fat_attributes("/fake/dir")
                assert attr & fat.FAT_ATTR_DIRECTORY
                assert not (attr & fat.FAT_ATTR_READ_ONLY)

                # Test setting attributes with fallback
                fat.set_fat_attributes("/fake/file", fat.FAT_ATTR_READ_ONLY)
                mock_chmod.assert_called()
    else:
        # Skip on non-Windows non-Linux platforms
        pytest.skip("Test only meaningful on Windows or Linux")
