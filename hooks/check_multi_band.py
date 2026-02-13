"""Pre-commit hook: validate multi-band PDK consistency."""

from __future__ import annotations

import sys
from pathlib import Path

from hooks._utils import CheckResult, find_band_dirs, find_package_dir


def main() -> int:
    result = CheckResult("check-multi-band")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        return 0

    bands = find_band_dirs(pkg_dir)
    if len(bands) < 2:
        # Not a multi-band PDK — skip silently
        return 0

    pkg_name = pkg_dir.name

    # 10a. Each band must have the same module set
    signatures: dict[str, dict[str, bool]] = {}
    for band in bands:
        sig = {
            "has_cells": (band / "cells").is_dir() or (band / "cells.py").exists(),
            "has_tech": (band / "tech.py").exists(),
            "has_models": (band / "models").is_dir() or (band / "models.py").exists(),
            "has_init": (band / "__init__.py").exists(),
        }
        signatures[band.name] = sig

        if not sig["has_init"]:
            result.error(f"{band}: missing __init__.py")
        if not sig["has_cells"]:
            result.error(f"{band}: missing cells module (cells/ or cells.py)")
        if not sig["has_tech"]:
            result.error(f"{band}: missing tech.py")

    # Cross-band consistency
    band_names = list(signatures.keys())
    reference_name = band_names[0]
    reference = signatures[reference_name]
    for band_name in band_names[1:]:
        for key, ref_val in reference.items():
            if signatures[band_name][key] != ref_val:
                result.warn(
                    f"Inconsistency: {reference_name} {key}={ref_val} "
                    f"but {band_name} {key}={signatures[band_name][key]}"
                )

    # 10b. Each band must have corresponding tests
    tests_dir = Path("tests")
    if tests_dir.is_dir():
        for band in bands:
            band_name = band.name
            # Check for test_<pdk>_<band>.py or <band>/test_pdk.py
            patterns = [
                tests_dir / f"test_{pkg_name}_{band_name}.py",
                tests_dir / f"test_{band_name}.py",
                tests_dir / band_name / "test_pdk.py",
                tests_dir / band_name / f"test_{pkg_name}.py",
            ]
            has_test = any(p.exists() for p in patterns)
            if not has_test:
                result.warn(
                    f"No test file found for band '{band_name}' "
                    f"(expected test_{pkg_name}_{band_name}.py or similar)"
                )

    # 10c. Shared layers at package root
    layers_in_bands: list[str] = []
    for band in bands:
        if (band / "layers.py").exists():
            layers_in_bands.append(band.name)

    if len(layers_in_bands) > 1:
        result.warn(
            f"layers.py found in multiple bands: {layers_in_bands} — "
            f"consider sharing layers at package root ({pkg_dir}/layers.py)"
        )

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
