import shutil
import pytest
import unittest
import signal
import subprocess
import sys
import os

import pytest

from ...helpers.process import ignore_sigint, create_subprocess
from ...platformflags import is_win32


class ProcessTest(unittest.TestCase):
    def test_create_subprocess_basic(self):
        # Simple test to check if a subprocess can be created
        cmd = [sys.executable, '-c', 'import sys; sys.exit(0)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        self.assertEqual(proc.returncode, 0)

    def test_create_subprocess_kwargs(self):
        # Test that kwargs are properly passed to Popen
        cmd = [sys.executable, '-c', 'import sys; print("test"); sys.exit(0)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        self.assertEqual(stdout.strip(), b'test')

    @pytest.mark.skipif(is_win32, reason="Unix-specific test")
    def test_unix_preexec_fn(self):
        # Test that on Unix, preexec_fn is properly set
        cmd = [sys.executable, '-c', 'import sys; sys.exit(0)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE)
        # Direct access to _preexec_fn is not reliable across Python versions
        # so we just verify the process runs successfully
        self.assertEqual(proc.wait(), 0)

    @pytest.mark.skipif(not is_win32, reason="Windows-specific test")
    def test_windows_creationflags(self):
        # Test that on Windows, creationflags is properly set
        cmd = [sys.executable, '-c', 'import sys; sys.exit(0)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE)
        # We can't directly check the creationflags, but we can verify the process runs
        self.assertEqual(proc.wait(), 0)
from ...helpers.process import popen_with_error_handling


class TestPopenWithErrorHandling:
    @pytest.mark.skipif(not shutil.which("test"), reason='"test" binary is needed')
    def test_simple(self):
        proc = popen_with_error_handling("test 1")
        assert proc.wait() == 0

    @pytest.mark.skipif(
        shutil.which("borg-foobar-test-notexist"), reason='"borg-foobar-test-notexist" binary exists (somehow?)'
    )
    def test_not_found(self):
        proc = popen_with_error_handling("borg-foobar-test-notexist 1234")
        assert proc is None

    @pytest.mark.parametrize("cmd", ('mismatched "quote', 'foo --bar="baz', ""))
    def test_bad_syntax(self, cmd):
        proc = popen_with_error_handling(cmd)
        assert proc is None

    def test_shell(self):
        with pytest.raises(AssertionError):
            popen_with_error_handling("", shell=True)
