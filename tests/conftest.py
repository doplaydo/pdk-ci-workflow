"""Shared fixtures for pre-commit hook tests.

Every hook operates on the *current working directory*, so the central pattern
is:

1. ``tmp_path`` gives us an isolated directory.
2. ``monkeypatch.chdir(tmp_path)`` moves the CWD there.
3. Helper fixtures scaffold a minimal valid PDK repository layout so that
   individual tests only need to tweak the part they are testing.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# Path to the example PDK repository layout shipped alongside the tests.
EXAMPLES_DIR = Path(__file__).parent / "examples"

# Prevent pytest from collecting test files inside the examples directory.
collect_ignore_glob = ["examples/**"]


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def pdk_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Scaffold a minimal valid PDK repo and chdir into it.

    Returns the tmp_path (== new CWD) so tests can mutate the tree.
    """
    monkeypatch.chdir(tmp_path)

    # Copy the entire example tree into the temporary directory.
    shutil.copytree(EXAMPLES_DIR, tmp_path, dirs_exist_ok=True)

    return tmp_path
