"""Pre-commit hook: enforce .github files match upstream templates.

Ruff-style auto-fix: on drift, rewrites local file from the canonical template
shipped inside this package, then exits 1. Second run sees no drift, exits 0.

Files to enforce are listed in TEMPLATES. Missing local files are skipped
(hook syncs existing files, does not create new ones).
"""

from __future__ import annotations

import difflib
import sys
from importlib.resources import files
from pathlib import Path

from hooks._utils import CheckResult, load_toml

# Paths (relative to PDK repo root) that must match the upstream template of
# the same relative path under `templates/` in pdk-ci-workflow.
TEMPLATES: list[str] = [
    ".github/dependabot.yml",
    ".github/release-drafter.yml",
    ".github/workflows/claude-pr-review.yml",
    ".github/workflows/drc.yml",
    ".github/workflows/issue.yml",
    ".github/workflows/model_coverage.yml",
    ".github/workflows/model_regression.yml",
    ".github/workflows/pages.yml",
    ".github/workflows/release-drafter.yml",
    ".github/workflows/test_code.yml",
    ".github/workflows/test_coverage.yml",
    ".github/workflows/update_badges.yml",
]


def _diff(old: str, new: str, path: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=2,
        )
    )


def _is_self_repo() -> bool:
    """Skip when running inside pdk-ci-workflow itself.

    This repo's `.github/` holds REUSABLE source workflows (not thin callers),
    so enforcing template content would clobber them. Identified by
    `pyproject.toml` project name.
    """
    data = load_toml("pyproject.toml")
    return bool(data and data.get("project", {}).get("name") == "ci-pdk-workflows")


def main() -> int:
    result = CheckResult("check-template-drift")

    if _is_self_repo():
        return 0

    root = files("templates")

    for rel in TEMPLATES:
        local = Path(rel)
        if not local.exists():
            continue

        parts = rel.split("/")
        src = root
        for p in parts:
            src = src.joinpath(p)
        if not src.is_file():
            result.error(f"no canonical template shipped for {rel}")
            continue

        src_text = src.read_text(encoding="utf-8")
        local_text = local.read_text(encoding="utf-8")

        if src_text == local_text:
            continue

        local.write_text(src_text, encoding="utf-8")
        print(_diff(local_text, src_text, rel))
        result.error(f"rewrote {rel} from upstream template")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
