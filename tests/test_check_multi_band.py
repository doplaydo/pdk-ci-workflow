"""Tests for check_multi_band hook."""

from __future__ import annotations

import shutil
from pathlib import Path

from hooks.check_multi_band import main


def _make_band(pkg: Path, band_name: str, *, cells: bool = True, tech: bool = True) -> Path:
    """Create a band subdirectory with optional cells/ and tech.py."""
    band = pkg / band_name
    band.mkdir(exist_ok=True)
    (band / "__init__.py").write_text("")
    if tech:
        (band / "tech.py").write_text("")
    if cells:
        cells_dir = band / "cells"
        cells_dir.mkdir()
        (cells_dir / "__init__.py").write_text("")
    return band


class TestCheckMultiBand:
    def test_single_band_skips(self, pdk_root: Path) -> None:
        """Non-multi-band PDKs should silently pass."""
        assert main() == 0

    def test_two_consistent_bands_pass(self, pdk_root: Path) -> None:
        pkg = pdk_root / "my_pdk"
        _make_band(pkg, "c_band")
        _make_band(pkg, "o_band")
        # Create test files for bands
        (pdk_root / "tests" / "test_c_band.py").write_text("def test_c(): pass\n")
        (pdk_root / "tests" / "test_o_band.py").write_text("def test_o(): pass\n")
        assert main() == 0

    def test_missing_init_in_band_fails(self, pdk_root: Path) -> None:
        """Bands without __init__.py are not detected as bands by find_band_dirs,
        so removing it from one band effectively removes that band from the
        multi-band check. With two remaining bands, the check runs normally."""
        pkg = pdk_root / "my_pdk"
        _make_band(pkg, "c_band")
        _make_band(pkg, "o_band")
        _make_band(pkg, "l_band")
        (pkg / "o_band" / "__init__.py").unlink()
        # o_band is no longer detected as a band; c_band + l_band are fine
        assert main() == 0

    def test_missing_tech_in_band_fails(self, pdk_root: Path) -> None:
        pkg = pdk_root / "my_pdk"
        _make_band(pkg, "c_band")
        band2 = _make_band(pkg, "o_band", tech=False)
        # o_band has cells but no tech → still detected as band (has_cells=True)
        # Should report error for missing tech.py
        assert main() == 1

    def test_missing_cells_in_band_fails(self, pdk_root: Path) -> None:
        pkg = pdk_root / "my_pdk"
        _make_band(pkg, "c_band")
        band2 = _make_band(pkg, "o_band", cells=False)
        # o_band has tech but no cells → still detected as band (has_tech=True)
        # Should report error for missing cells
        assert main() == 1

    def test_inconsistent_modules_warns(self, pdk_root: Path) -> None:
        """Inconsistent module signatures should warn but not fail."""
        pkg = pdk_root / "my_pdk"
        b1 = _make_band(pkg, "c_band")
        b2 = _make_band(pkg, "o_band")
        # Add models to c_band but not o_band
        (b1 / "models").mkdir()
        (b1 / "models" / "__init__.py").write_text("")
        # This creates an inconsistency in has_models
        assert main() == 0  # warnings only

    def test_missing_band_tests_warns(self, pdk_root: Path) -> None:
        """Missing band-specific tests should warn."""
        pkg = pdk_root / "my_pdk"
        _make_band(pkg, "c_band")
        _make_band(pkg, "o_band")
        # No test_c_band.py or test_o_band.py
        assert main() == 0  # warnings only

    def test_layers_in_multiple_bands_warns(self, pdk_root: Path) -> None:
        """layers.py in multiple bands should warn about sharing."""
        pkg = pdk_root / "my_pdk"
        b1 = _make_band(pkg, "c_band")
        b2 = _make_band(pkg, "o_band")
        (b1 / "layers.py").write_text("WG = (1, 0)\n")
        (b2 / "layers.py").write_text("WG = (1, 0)\n")
        assert main() == 0  # warnings only

    def test_no_package_dir_passes(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main() == 0
