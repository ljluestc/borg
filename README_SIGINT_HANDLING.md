# SIGINT Handling in Borg

## Overview

When users press Ctrl-C (sending a SIGINT signal), Borg needs to handle this gracefully. The main process should catch the signal and perform a clean shutdown, while subprocesses (like SSH connections or tar commands) should ignore the signal and continue running until they complete naturally.

## Implementation

Borg implements platform-specific SIGINT handling through the `create_subprocess()` function in `src/borg/helpers/process.py`:

### Unix Platforms

On Unix-like platforms (Linux, macOS, BSD), Borg uses Python's `preexec_fn` parameter to set up SIGINT handling in subprocesses:

```python
def ignore_sigint():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

subprocess.Popen(cmd, preexec_fn=ignore_sigint, ...)
```

This causes the subprocess to ignore SIGINT signals, allowing the main Borg process to handle the signal and shut down gracefully.

### Windows Platforms

On Windows, `preexec_fn` is not available. Instead, Borg uses the `CREATE_NEW_PROCESS_GROUP` flag to create a new process group that won't receive Ctrl-C signals from the console:

```python
subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, ...)
```

This achieves the same effect: the main Borg process can handle Ctrl-C, while the subprocesses continue running.

## Usage

Instead of using `subprocess.Popen()` directly, code should use the `create_subprocess()` function which handles the platform-specific details automatically:

```python
from borg.helpers.process import create_subprocess

proc = create_subprocess(command, stdout=subprocess.PIPE, ...)
```

This function will apply the appropriate platform-specific settings to ensure correct SIGINT handling.
