"""Tests for check_test_structure hook."""

from __future__ import annotations

import shutil
from pathlib import Path

from hooks.check_test_structure import main


class TestCheckTestStructure:
    def test_valid_test_dir_passes(self, pdk_root: Path) -> None:
        # Add difftest and data_regression content to prevent warnings
        (pdk_root / "tests" / "test_pdk.py").write_text(
            "def test_a(): pass\ndef test_difftest(): difftest()\ndef test_reg(): data_regression.check()\n"
        )
        assert main() == 0

    def test_missing_tests_dir_fails(self, pdk_root: Path) -> None:
        shutil.rmtree(pdk_root / "tests")
        assert main() == 1

    def test_no_test_files_fails(self, pdk_root: Path) -> None:
        (pdk_root / "tests" / "test_pdk.py").unlink()
        assert main() == 1

    def test_missing_gds_ref_warns(self, pdk_root: Path) -> None:
        """Missing GDS reference directory is a warning, not error."""
        shutil.rmtree(pdk_root / "tests" / "gds_ref")
        assert main() == 0

    def test_missing_difftest_warns(self, pdk_root: Path) -> None:
        """No difftest() calls should warn but not fail."""
        (pdk_root / "tests" / "test_pdk.py").write_text(
            "def test_something(): pass\n"
        )
        assert main() == 0

    def test_missing_data_regression_warns(self, pdk_root: Path) -> None:
        """No data_regression usage should warn but not fail."""
        (pdk_root / "tests" / "test_pdk.py").write_text(
            "def test_something(): pass\n"
        )
        assert main() == 0

    def test_nested_test_files_found(self, pdk_root: Path) -> None:
        """test_*.py files in subdirectories should be found."""
        (pdk_root / "tests" / "test_pdk.py").unlink()
        sub = pdk_root / "tests" / "subdir"
        sub.mkdir()
        (sub / "test_nested.py").write_text("def test_x(): pass\n")
        assert main() == 0

    def test_gds_ref_variants_accepted(self, pdk_root: Path) -> None:
        """Various GDS reference directory naming patterns should be accepted."""
        shutil.rmtree(pdk_root / "tests" / "gds_ref")
        # Use _gds variant
        (pdk_root / "tests" / "my_pdk_gds").mkdir()
        (pdk_root / "tests" / "test_pdk.py").write_text(
            "def test_a(): difftest(); data_regression.check()\n"
        )
        assert main() == 0
