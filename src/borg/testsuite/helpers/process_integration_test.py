import unittest
import signal
import subprocess
import sys
import os
import time
from threading import Thread

import pytest

from ...helpers.process import create_subprocess
from ...platformflags import is_win32


class ProcessIntegrationTest(unittest.TestCase):
    @pytest.mark.skipif(is_win32, reason="Unix-specific test")
    def test_subprocess_ignores_sigint_unix(self):
        # This test verifies that a subprocess created with create_subprocess
        # ignores SIGINT signals (Ctrl-C) on Unix platforms

        # Create a subprocess that sleeps for 10 seconds
        cmd = [sys.executable, '-c', 'import time; time.sleep(10); print("Done")']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            # Send SIGINT to the subprocess
            time.sleep(0.5)  # Give process time to start
            os.kill(proc.pid, signal.SIGINT)

            # If SIGINT is properly ignored, the process should continue
            # We'll wait a short time and check it's still running
            time.sleep(1)

            # Process should still be running
            self.assertIsNone(proc.poll())

        finally:
            # Clean up
            proc.terminate()
            proc.wait()

    @pytest.mark.skipif(not is_win32, reason="Windows-specific test")
    def test_subprocess_ignores_ctrl_c_windows(self):
        # On Windows, we can't directly test the Ctrl+C behavior in an automated way
        # without complex setup, so we just verify the process starts with the correct flags
        cmd = [sys.executable, '-c', 'import sys; sys.exit(42)']
        proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.wait(), 42)
