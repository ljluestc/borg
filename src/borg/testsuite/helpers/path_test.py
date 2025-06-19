import unittest
import pytest

from ...helpers.path import safe_path, original_path
from ...platformflags import is_win32, mapchars


class PathTest(unittest.TestCase):
    def test_safe_path_no_change_for_normal_path(self):
        path = "normal/path/example.txt"
        self.assertEqual(path, safe_path(path))

    @pytest.mark.skipif(not is_win32, reason="Windows-specific test")
    def test_safe_path_windows_chars(self):
        path = "file*with?invalid<chars>in|name:txt"
        safe = safe_path(path)

        # Verify characters were remapped
        self.assertNotEqual(path, safe)
        self.assertNotIn("*", safe)
        self.assertNotIn("?", safe)
        self.assertNotIn("<", safe)
        self.assertNotIn(">", safe)
        self.assertNotIn("|", safe)
        self.assertNotIn(":", safe)

        # Verify we can convert back to original
        self.assertEqual(path, original_path(safe))

    @pytest.mark.skipif(is_win32, reason="Non-Windows test")
    def test_safe_path_non_windows(self):
        path = "file*with?invalid<chars>in|name:txt"
        self.assertEqual(path, safe_path(path))
        self.assertEqual(path, original_path(path))

    @pytest.mark.skipif(not is_win32, reason="Windows-specific test")
    def test_path_roundtrip(self):
        paths = [
            "normal/path/example.txt",
            "file*with?invalid<chars>in|name:txt",
            "mixed_path*with:some|invalid?chars.dat"
        ]

        for path in paths:
            safe = safe_path(path)
            original = original_path(safe)
            self.assertEqual(path, original)
