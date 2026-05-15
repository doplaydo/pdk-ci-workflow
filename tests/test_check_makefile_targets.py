"""Tests for check_makefile_targets hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hooks.check_makefile_targets import main


class TestCheckMakefileTargets:
    def test_valid_makefile_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_no_makefile_fails(self, pdk_root: Path) -> None:
        (pdk_root / "Makefile").unlink()
        assert main() == 1

    def test_missing_install_target_fails(self, pdk_root: Path) -> None:
        (pdk_root / "Makefile").write_text("test:\n\tpytest\n")
        assert main() == 1

    def test_missing_test_target_fails(self, pdk_root: Path) -> None:
        (pdk_root / "Makefile").write_text("install:\n\tuv sync\n")
        assert main() == 1

    def test_pip_install_warns(self, pdk_root: Path) -> None:
        """Using pip instead of uv should not fail but should warn."""
        (pdk_root / "Makefile").write_text(
            textwrap.dedent("""\
                install:
                \tpip install -e .

                test:
                \tpytest
            """)
        )
        # Should still pass (warnings only for pip usage)
        assert main() == 0

    def test_test_without_pytest_warns(self, pdk_root: Path) -> None:
        """test target without pytest should warn but not fail."""
        (pdk_root / "Makefile").write_text(
            textwrap.dedent("""\
                install:
                \tuv sync

                test:
                \tpython -m unittest
            """)
        )
        assert main() == 0

    def test_recommended_targets_missing_only_warns(
        self, pdk_root: Path
    ) -> None:
        """Missing recommended targets should not fail the hook."""
        (pdk_root / "Makefile").write_text(
            textwrap.dedent("""\
                install:
                \tuv sync

                test:
                \tuv run pytest
            """)
        )
        assert main() == 0

    def test_setup_py_build_warns(self, pdk_root: Path) -> None:
        """build target using setup.py should warn but not fail."""
        (pdk_root / "Makefile").write_text(
            textwrap.dedent("""\
                install:
                \tuv sync

                test:
                \tpytest

                build:
                \tpython setup.py sdist
            """)
        )
        assert main() == 0
