"""Pre-commit hook: validate PDK test directory structure and regression tests."""

from __future__ import annotations

import sys
from pathlib import Path

from hooks._utils import CheckResult


def main() -> int:
    result = CheckResult("check-test-structure")

    tests_dir = Path("tests")

    # 7a. tests/ directory must exist
    if not tests_dir.is_dir():
        result.error("tests/ directory missing at repo root")
        return result.report()

    # 7b. Must have at least one test_*.py file
    test_files = list(tests_dir.rglob("test_*.py"))
    if not test_files:
        result.error("No test_*.py files found in tests/")
        return result.report()

    # 7c. GDS reference directory must exist
    gds_ref_dirs = (
        list(tests_dir.rglob("gds_ref"))
        + list(tests_dir.rglob("*_gds_ref"))
        + [d for d in tests_dir.rglob("*_gds") if d.is_dir()]
    )
    if not gds_ref_dirs:
        result.warn(
            "No GDS reference directory found in tests/ "
            "(expected gds_ref/ or *_gds_ref/ or *_gds/)"
        )

    # 7d. At least one test must call difftest()
    has_difftest = False
    for tf in test_files:
        content = tf.read_text()
        if "difftest" in content:
            has_difftest = True
            break
    if not has_difftest:
        result.warn("No test file calls difftest() for GDS regression testing")

    # 7e. At least one test must call data_regression.check()
    has_data_regression = False
    for tf in test_files:
        content = tf.read_text()
        if "data_regression" in content:
            has_data_regression = True
            break
    if not has_data_regression:
        result.warn(
            "No test file uses data_regression for settings regression testing"
        )

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
