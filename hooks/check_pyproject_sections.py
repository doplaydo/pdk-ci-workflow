"""Pre-commit hook: validate pyproject.toml has all required PDK sections."""

from __future__ import annotations

import sys
from typing import Any

from hooks._utils import CheckResult, find_package_dir, load_toml


# ── Sub-check functions ──────────────────────────────────────────────


def check_build_system(data: dict[str, Any], result: CheckResult) -> None:
    """2a: [build-system] must have build-backend and requires."""
    bs = data.get("build-system")
    if bs is None:
        result.error("[build-system] section missing")
        return
    if "requires" not in bs:
        result.error("[build-system].requires missing")
    if "build-backend" not in bs:
        result.error("[build-system].build-backend missing")


def check_project_fields(data: dict[str, Any], result: CheckResult) -> None:
    """2b: [project] required fields."""
    proj = data.get("project")
    if proj is None:
        result.error("[project] section missing")
        return

    required = ["name", "version", "description", "requires-python"]
    for field in required:
        if field not in proj:
            result.error(f"[project].{field} missing")

    # readme must be "README.md"
    readme = proj.get("readme")
    if readme is None:
        result.error('[project].readme missing (must be "README.md")')
    elif readme != "README.md":
        result.error(f'[project].readme = "{readme}" (must be "README.md")')

    # authors
    authors = proj.get("authors")
    if not authors:
        result.error("[project].authors missing or empty")

    # license must be {file = "LICENSE"}
    lic = proj.get("license")
    if lic is None:
        result.error("[project].license missing")
    elif not (isinstance(lic, dict) and lic.get("file") == "LICENSE"):
        result.error('[project].license must be {file = "LICENSE"}')

    # keywords must include "python"
    keywords = proj.get("keywords")
    if keywords is None:
        result.error("[project].keywords missing")
    elif "python" not in keywords:
        result.error('[project].keywords must include "python"')

    # classifiers
    if "classifiers" not in proj:
        result.warn("[project].classifiers missing (recommended)")

    # dependencies must include gdsfactory
    deps = proj.get("dependencies")
    if deps is None:
        result.error("[project].dependencies missing")
    else:
        has_gds = any("gdsfactory" in str(d) for d in deps)
        if not has_gds:
            result.error("[project].dependencies must include gdsfactory")


def check_optional_deps(data: dict[str, Any], result: CheckResult) -> None:
    """2c: [project.optional-dependencies] required groups."""
    opt_deps = data.get("project", {}).get("optional-dependencies", {})
    dep_groups = data.get("dependency-groups", {})

    # dev group
    dev_deps = opt_deps.get("dev", dep_groups.get("dev", []))
    if not dev_deps:
        result.error(
            "[project.optional-dependencies].dev missing "
            "(need pytest, pytest-cov, pytest_regressions, pre-commit)"
        )
    else:
        dev_str = " ".join(str(d) for d in dev_deps).lower()
        for pkg in ["pytest", "pytest-cov", "pytest_regressions", "pre-commit"]:
            normalized = pkg.replace("_", "-").replace("-", "")
            if normalized not in dev_str.replace("_", "").replace("-", ""):
                result.warn(f"[project.optional-dependencies].dev missing {pkg}")

    # docs group
    docs_deps = opt_deps.get("docs", dep_groups.get("docs", []))
    if not docs_deps:
        result.warn(
            "[project.optional-dependencies].docs missing "
            "(recommended: jupytext, jupyter-book)"
        )
    else:
        docs_str = " ".join(str(d) for d in docs_deps).lower()
        for pkg in ["jupytext", "jupyter-book"]:
            if pkg not in docs_str:
                result.warn(f"[project.optional-dependencies].docs missing {pkg}")


def check_ruff(data: dict[str, Any], result: CheckResult) -> None:
    """2d: [tool.ruff] structure and lint config."""
    ruff = data.get("tool", {}).get("ruff")
    if ruff is None:
        result.error("[tool.ruff] section missing")
        return

    # fix = true
    if not ruff.get("fix"):
        result.warn("[tool.ruff].fix = true not set")

    # select/ignore must be under [tool.ruff.lint], NOT [tool.ruff]
    if "select" in ruff:
        result.error(
            "[tool.ruff].select should be under [tool.ruff.lint].select"
        )
    if "ignore" in ruff:
        result.error(
            "[tool.ruff].ignore should be under [tool.ruff.lint].ignore"
        )

    lint = ruff.get("lint", {})

    # Minimum select values
    select = lint.get("select", [])
    required_select = {"B", "C", "D", "E", "F", "I", "T10", "UP", "W"}
    missing_select = required_select - set(select)
    if missing_select:
        result.warn(
            f"[tool.ruff.lint].select missing: {sorted(missing_select)}"
        )

    # Minimum ignore values
    ignore = lint.get("ignore", [])
    required_ignore = {"E501", "B008", "C901", "B905", "C408"}
    missing_ignore = required_ignore - set(ignore)
    if missing_ignore:
        result.warn(
            f"[tool.ruff.lint].ignore missing: {sorted(missing_ignore)}"
        )

    # pydocstyle convention under [tool.ruff.lint.pydocstyle]
    pydocstyle = lint.get("pydocstyle", {})
    if not pydocstyle.get("convention"):
        # Check deprecated standalone [tool.pydocstyle]
        standalone = data.get("tool", {}).get("pydocstyle", {})
        if standalone.get("convention"):
            result.warn(
                "[tool.pydocstyle].convention is deprecated — "
                "move to [tool.ruff.lint.pydocstyle].convention"
            )
        else:
            result.warn(
                '[tool.ruff.lint.pydocstyle].convention not set '
                '(recommend "google")'
            )


def check_ruff_per_file_ignores(data: dict[str, Any], result: CheckResult) -> None:
    """2e: [tool.ruff.lint.per-file-ignores] for cells/__init__.py."""
    pkg_dir = find_package_dir()
    if pkg_dir is None:
        return

    lint = data.get("tool", {}).get("ruff", {}).get("lint", {})
    per_file = lint.get("per-file-ignores", {})

    for submod in ["cells", "models"]:
        init_path = pkg_dir / submod / "__init__.py"
        if init_path.exists():
            # Check if any key matches the init path with F403 in its ignores
            found = False
            for pattern, ignores in per_file.items():
                if submod in pattern and "__init__" in pattern:
                    if "F403" in ignores:
                        found = True
                        break
            if not found:
                result.warn(
                    f"[tool.ruff.lint.per-file-ignores] should ignore F403 "
                    f"for {submod}/__init__.py"
                )


def check_codespell(data: dict[str, Any], result: CheckResult) -> None:
    """2f: [tool.codespell] section."""
    codespell = data.get("tool", {}).get("codespell")
    if codespell is None:
        result.error("[tool.codespell] section missing")
        return

    ignore_words = codespell.get("ignore-words-list", "")
    if isinstance(ignore_words, list):
        words = set(ignore_words)
    else:
        words = {w.strip() for w in str(ignore_words).split(",")}

    required_words = {"te", "ba", "fpr", "ro", "nd", "donot", "schem"}
    missing = required_words - words
    if missing:
        result.warn(
            f"[tool.codespell].ignore-words-list missing: {sorted(missing)}"
        )


def check_pytest(data: dict[str, Any], result: CheckResult) -> None:
    """2g: [tool.pytest.ini_options] section."""
    pytest_cfg = data.get("tool", {}).get("pytest", {}).get("ini_options")
    if pytest_cfg is None:
        result.error("[tool.pytest.ini_options] section missing")
        return
    if "testpaths" not in pytest_cfg:
        result.error("[tool.pytest.ini_options].testpaths missing")
    if "addopts" not in pytest_cfg:
        result.warn("[tool.pytest.ini_options].addopts missing (recommend '--tb=short')")


def check_package_data(data: dict[str, Any], result: CheckResult) -> None:
    """2h: [tool.setuptools.package-data] section."""
    pkg_data = data.get("tool", {}).get("setuptools", {}).get("package-data")
    if pkg_data is None:
        result.error("[tool.setuptools.package-data] section missing")
        return

    if "*" not in pkg_data:
        result.error(
            '[tool.setuptools.package-data] must use wildcard key "*" '
            "(not a package-specific key)"
        )
        return

    patterns = pkg_data["*"]
    required_exts = ["*.csv", "*.yaml", "*.yml", "*.gds", "*.lyp", "*.oas", "*.lyt"]
    for ext in required_exts:
        if ext not in patterns:
            result.warn(
                f"[tool.setuptools.package-data].* missing {ext}"
            )


def check_tbump(data: dict[str, Any], result: CheckResult) -> None:
    """2i: [tool.tbump] section."""
    tbump = data.get("tool", {}).get("tbump")
    if tbump is None:
        result.error("[tool.tbump] section missing")
        return

    # version.current
    version = tbump.get("version", {})
    if "current" not in version:
        result.error("[tool.tbump.version].current missing")
    else:
        # Cross-check with [project].version
        proj_version = data.get("project", {}).get("version")
        if proj_version and version["current"] != proj_version:
            result.error(
                f"[tool.tbump.version].current = \"{version['current']}\" "
                f"does not match [project].version = \"{proj_version}\""
            )

    # file entries
    files = tbump.get("file", [])
    if not files:
        result.error("[[tool.tbump.file]] entries missing")
    else:
        srcs = {f.get("src") for f in files if isinstance(f, dict)}
        if "pyproject.toml" not in srcs:
            result.error("[[tool.tbump.file]] missing src = 'pyproject.toml'")
        if "README.md" not in srcs:
            result.warn("[[tool.tbump.file]] missing src = 'README.md'")
        # Check for __init__.py tracking
        has_init = any("__init__.py" in (s or "") for s in srcs)
        if not has_init:
            result.error(
                "[[tool.tbump.file]] missing src for <pkg>/__init__.py"
            )

    # git section
    git = tbump.get("git", {})
    if "message_template" not in git:
        result.error("[tool.tbump.git].message_template missing")
    if "tag_template" not in git:
        result.error("[tool.tbump.git].tag_template missing")


def check_mypy(data: dict[str, Any], result: CheckResult) -> None:
    """2j: [tool.mypy] section."""
    mypy = data.get("tool", {}).get("mypy")
    if mypy is None:
        result.error("[tool.mypy] section missing")
        return
    if not mypy.get("strict"):
        result.warn("[tool.mypy].strict = true not set (recommended)")


def check_towncrier(data: dict[str, Any], result: CheckResult) -> None:
    """2k: [tool.towncrier] section."""
    tc = data.get("tool", {}).get("towncrier")
    if tc is None:
        result.warn("[tool.towncrier] section missing (recommended)")
        return

    expected = {
        "directory": ".changelog.d",
        "filename": "CHANGELOG.md",
        "template": ".changelog.d/changelog_template.jinja",
    }
    for key, expected_val in expected.items():
        actual = tc.get(key)
        if actual is None:
            result.warn(f"[tool.towncrier].{key} missing (expected \"{expected_val}\")")
        elif actual != expected_val:
            result.warn(
                f"[tool.towncrier].{key} = \"{actual}\" "
                f"(expected \"{expected_val}\")"
            )


# ── Registry ─────────────────────────────────────────────────────────

SUB_CHECKS = [
    check_build_system,
    check_project_fields,
    check_optional_deps,
    check_ruff,
    check_ruff_per_file_ignores,
    check_codespell,
    check_pytest,
    check_package_data,
    check_tbump,
    check_mypy,
    check_towncrier,
]


def main() -> int:
    data = load_toml("pyproject.toml")
    if data is None:
        print("\u26a0\ufe0f  No pyproject.toml found — skipping.")
        return 0

    result = CheckResult("check-pyproject-sections")
    for check_fn in SUB_CHECKS:
        check_fn(data, result)

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
