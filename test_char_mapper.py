import unittest
import sys
from char_mapper import map_invalid_chars, unmap_chars, INVALID_CHARS, OFFSET, is_win32

class TestCharMapper(unittest.TestCase):
    def test_map_invalid_chars(self):
        original = "test*file?name<with>special|chars:end"
        mapped = map_invalid_chars(original)

        if is_win32:
            # On Windows, characters should be remapped
            self.assertNotEqual(original, mapped)
            for char in INVALID_CHARS:
                self.assertNotIn(char, mapped)

            # Test that normal characters remain unchanged
            self.assertIn('test', mapped)
            self.assertIn('file', mapped)
            self.assertIn('name', mapped)
            self.assertIn('with', mapped)
            self.assertIn('special', mapped)
            self.assertIn('chars', mapped)
            self.assertIn('end', mapped)

            # Test that remapped characters are in the expected range
            for char in mapped:
                if char not in original or char in INVALID_CHARS:
                    self.assertTrue(OFFSET <= ord(char) <= OFFSET + 0xFF,
                                  f"Character {char} (U+{ord(char):04X}) should be in private use area")
        else:
            # On non-Windows platforms, string should remain unchanged
            self.assertEqual(original, mapped)

    def test_roundtrip_conversion(self):
        original = "test*file?name<with>special|chars:end"
        mapped = map_invalid_chars(original)
        unmapped = unmap_chars(mapped)

        # After round-trip conversion, we should get the original string back
        self.assertEqual(original, unmapped)

    def test_normal_path_unchanged(self):
        normal_path = "normal/path/without/special/chars.txt"
        mapped = map_invalid_chars(normal_path)

        # Normal paths should remain unchanged
        self.assertEqual(normal_path, mapped)

if __name__ == '__main__':
    unittest.main()
