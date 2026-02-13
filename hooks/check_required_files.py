"""Pre-commit hook: verify required PDK repository files exist."""

from __future__ import annotations

import sys
from pathlib import Path

from hooks._utils import CheckResult

REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
    ".gitignore",
    ".pre-commit-config.yaml",
]

REQUIRED_DIRS = [
    "tests",
]

REQUIRED_WORKFLOWS = [
    ".github/workflows/release-drafter.yml",
]

# test_code.yml OR test.yml (quantum-rf-pdk uses test.yml)
TEST_WORKFLOW_CANDIDATES = [
    ".github/workflows/test_code.yml",
    ".github/workflows/test.yml",
]

RECOMMENDED_FILES = [
    ".gitattributes",
    ".changelog.d/changelog_template.jinja",
    ".github/workflows/release.yml",
]


def main() -> int:
    result = CheckResult("check-required-files")

    for f in REQUIRED_FILES:
        if not Path(f).exists():
            result.error(f"Required file missing: {f}")

    for d in REQUIRED_DIRS:
        if not Path(d).is_dir():
            result.error(f"Required directory missing: {d}/")

    for f in REQUIRED_WORKFLOWS:
        if not Path(f).exists():
            result.error(f"Required workflow missing: {f}")

    # test_code.yml or test.yml — at least one must exist
    if not any(Path(c).exists() for c in TEST_WORKFLOW_CANDIDATES):
        result.error(
            "Required workflow missing: .github/workflows/test_code.yml "
            "(or test.yml)"
        )

    for f in RECOMMENDED_FILES:
        if not Path(f).exists():
            result.warn(f"Recommended file missing: {f}")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
