"""Pre-commit hook: verify version strings are consistent across all config files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hooks._utils import CheckResult, find_package_dir, get_assigned_string, load_toml, parse_file


def main() -> int:
    result = CheckResult("check-version-sync")

    data = load_toml("pyproject.toml")
    if data is None:
        result.warn("No pyproject.toml found — skipping version sync check.")
        return result.report()

    versions: dict[str, str] = {}

    # 1. [project].version
    proj_version = data.get("project", {}).get("version")
    if proj_version:
        versions["pyproject.toml [project].version"] = proj_version

    # 2. [tool.tbump.version].current
    tbump_version = (
        data.get("tool", {}).get("tbump", {}).get("version", {}).get("current")
    )
    if tbump_version:
        versions["pyproject.toml [tool.tbump.version].current"] = tbump_version

    # 3. <pkg>/__init__.py __version__
    pkg_dir = find_package_dir()
    if pkg_dir:
        init_path = pkg_dir / "__init__.py"
        if init_path.exists():
            tree = parse_file(init_path)
            if tree:
                init_version = get_assigned_string(tree, "__version__")
                if init_version:
                    versions[f"{init_path} __version__"] = init_version

    # 4. README.md pip install version (optional, e.g. pip install mypkg==1.2.3)
    readme = Path("README.md")
    if readme.exists():
        content = readme.read_text()
        m = re.search(
            r"pip\s+install\s+[\w-]+==([\d]+\.[\d]+\.[\d]+[^\s\"']*)",
            content,
        )
        if m:
            versions["README.md pip install version"] = m.group(1)

    # Compare
    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        result.error("Version mismatch detected:")
        for location, ver in sorted(versions.items()):
            result.error(f"  {location}: {ver}")
    elif len(versions) < 2:
        result.warn(
            "Version found in fewer than 2 locations — cannot fully verify sync."
        )

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
