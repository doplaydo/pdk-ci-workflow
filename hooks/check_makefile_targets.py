"""Pre-commit hook: validate Makefile has required targets."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hooks._utils import CheckResult

REQUIRED_TARGETS = {"install", "test"}
RECOMMENDED_TARGETS = {"test-force", "docs", "build", "update-pre"}


def _get_target_bodies(content: str) -> dict[str, str]:
    """Parse Makefile and return target_name -> body text for each target."""
    targets: dict[str, str] = {}
    current_target: str | None = None
    body_lines: list[str] = []

    for line in content.split("\n"):
        # New target definition
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:", line)
        if m:
            if current_target is not None:
                targets[current_target] = "\n".join(body_lines)
            current_target = m.group(1)
            body_lines = []
        elif current_target is not None:
            body_lines.append(line)

    if current_target is not None:
        targets[current_target] = "\n".join(body_lines)

    return targets


def main() -> int:
    result = CheckResult("check-makefile-targets")

    makefile = Path("Makefile")
    if not makefile.exists():
        result.error("Makefile not found")
        return result.report()

    content = makefile.read_text()
    targets = _get_target_bodies(content)
    target_names = set(targets.keys())

    for t in REQUIRED_TARGETS:
        if t not in target_names:
            result.error(f"Makefile missing required target: {t}")

    for t in RECOMMENDED_TARGETS:
        if t not in target_names:
            result.warn(f"Makefile missing recommended target: {t}")

    # Content checks for existing targets
    if "install" in targets:
        body = targets["install"]
        if "uv" not in body and "pip" in body:
            result.warn(
                "Makefile 'install' target uses pip — consider migrating to 'uv sync'"
            )

    if "test" in targets:
        body = targets["test"]
        if "pytest" not in body:
            result.warn("Makefile 'test' target does not appear to run pytest")

    if "build" in targets:
        body = targets["build"]
        if "setup.py" in body:
            result.warn(
                "Makefile 'build' target uses setup.py — "
                "consider migrating to 'uv build' or 'python -m build'"
            )

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
