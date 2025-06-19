import unittest
import signal
import subprocess
import sys
import os
import time
from contextlib import contextmanager

import pytest

from ...helpers.process import create_subprocess
from ...platformflags import is_win32


class ProcessCtrlCTest(unittest.TestCase):
    """
    Tests for handling Ctrl-C (SIGINT) in subprocesses.
    """

    @pytest.mark.skipif(is_win32, reason="Unix-specific test")
    def test_unix_subprocess_ignores_sigint(self):
        # This test verifies that on Unix platforms, a subprocess created with
        # create_subprocess() ignores SIGINT signals

        # Create a Python subprocess that just sleeps
        cmd = [sys.executable, '-c', 'import time, sys; time.sleep(3); sys.exit(0)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            # Allow process to start
            time.sleep(0.5)

            # Send SIGINT to the subprocess
            os.kill(proc.pid, signal.SIGINT)

            # Wait a bit to let signal be processed
            time.sleep(0.5)

            # Process should still be running (not terminated by SIGINT)
            self.assertIsNone(proc.poll(), "Process was terminated by SIGINT when it should have ignored it")

        finally:
            # Clean up
            proc.terminate()
            proc.wait(timeout=1)

    @pytest.mark.skipif(not is_win32, reason="Windows-specific test")
    def test_windows_subprocess_starts_correctly(self):
        # On Windows we can't easily test the Ctrl-C handling directly in an automated test
        # Instead, we verify that the process starts correctly with the appropriate flags

        cmd = [sys.executable, '-c', 'import time, sys; time.sleep(1); sys.exit(42)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Process should run and exit with the specified code
        self.assertEqual(proc.wait(), 42)
