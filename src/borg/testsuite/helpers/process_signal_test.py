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


@contextmanager
def main_process_handling_sigint():
    """
    Context manager that sets up SIGINT handling in the main process.

    This simulates what happens when a user presses Ctrl-C: the main process
    receives SIGINT and can handle it while child processes should ignore it.
    """
    if is_win32:
        # Not applicable on Windows
        yield
        return

    # Store original handler
    original_handler = signal.getsignal(signal.SIGINT)

    # Setup flag to track if handler was called
    handler_called = [False]

    def test_handler(sig, frame):
        handler_called[0] = True

    try:
        # Install test handler
        signal.signal(signal.SIGINT, test_handler)
        yield handler_called
    finally:
        # Restore original handler
        signal.signal(signal.SIGINT, original_handler)


class ProcessSignalTest(unittest.TestCase):
    @pytest.mark.skipif(is_win32, reason="Unix-specific test")
    def test_sigint_main_process_vs_subprocess(self):
        """
        Test that SIGINT is handled differently in main vs. subprocess.

        The main process should handle SIGINT (Ctrl-C), while
        the subprocess should ignore it completely.
        """
        with main_process_handling_sigint() as handler_called:
            # Start a subprocess that will run for a few seconds
            cmd = [sys.executable, '-c', 'import time, sys; time.sleep(3); sys.exit(0)']
            proc = create_subprocess(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            try:
                # Wait for process to start
                time.sleep(0.5)

                # Send SIGINT to the process group (simulating Ctrl-C)
                # This should be caught by both the main process and subprocess
                os.kill(0, signal.SIGINT)

                # Give time for signal handlers to run
                time.sleep(0.5)

                # Main process should have handled SIGINT
                self.assertTrue(handler_called[0], "Main process didn't handle SIGINT")

                # Subprocess should have ignored SIGINT and still be running
                self.assertIsNone(proc.poll(), "Subprocess was terminated by SIGINT")

            finally:
                # Clean up
                proc.terminate()
                proc.wait(timeout=1)
