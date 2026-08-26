"""Keep Python stdout separate from native writes to file descriptor 1.

This module is loaded only when a serial-confirmation child receives its
directory through ``PYTHONPATH``.  Python output retains a duplicate of the
original stdout pipe.  Native libraries that later write directly to fd 1 are
captured by the child's stderr pipe instead.
"""

from __future__ import annotations

import hashlib
import os
import sys


_source_path = os.path.realpath(__file__)
with open(_source_path, "rb") as _source_handle:
    _source_sha256 = hashlib.sha256(_source_handle.read()).hexdigest()
_expected_sha256 = os.environ.get("QLDPC_STDOUT_ISOLATOR_EXPECTED_SHA256")
if _source_sha256 != _expected_sha256:
    raise RuntimeError("stdout isolator source hash does not match child environment")

_original_stdout = sys.stdout
_original_stdout.flush()
sys.stderr.flush()
_python_stdout_fd = os.dup(_original_stdout.fileno())
os.dup2(sys.stderr.fileno(), _original_stdout.fileno())
sys.stdout = os.fdopen(
    _python_stdout_fd,
    "w",
    buffering=1,
    encoding=_original_stdout.encoding or "utf-8",
    errors=_original_stdout.errors or "strict",
    closefd=True,
)
sys.stderr.write(f"QLDPC_STDOUT_ISOLATION_V1:{_source_sha256}\n")
sys.stderr.flush()
