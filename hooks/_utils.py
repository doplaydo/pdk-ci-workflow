"""Shared utilities for PDK template compliance hooks."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import yaml


# ── TOML / YAML loading ─────────────────────────────────────────────


def load_toml(path: str = "pyproject.toml") -> dict[str, Any] | None:
    """Load and parse a TOML file. Returns None if the file doesn't exist."""
    p = Path(path)
    if not p.exists():
        return None
    with p.open("rb") as f:
        return tomllib.load(f)


def load_yaml(path: str) -> dict[str, Any] | None:
    """Load and parse a YAML file. Returns None if the file doesn't exist."""
    p = Path(path)
    if not p.exists():
        return None
    with p.open() as f:
        return yaml.safe_load(f)


# ── Package discovery ────────────────────────────────────────────────

_SKIP_DIRS = {"tests", "docs", "notebooks", ".git", ".github", "actions", "hooks", "scripts"}


def find_package_dir() -> Path | None:
    """Discover the PDK package directory from pyproject.toml.

    Strategy:
    1. Parse [tool.setuptools.packages.find].include for the root package name.
    2. Fallback: normalize [project].name (hyphens to underscores), look for dir.
    3. Last resort: scan for directories with __init__.py, skip known non-packages.
    """
    data = load_toml("pyproject.toml")
    if data is None:
        return None

    # Try [tool.setuptools.packages.find].include
    find_cfg = (
        data.get("tool", {})
        .get("setuptools", {})
        .get("packages", {})
        .get("find", {})
    )
    where = find_cfg.get("where", ["."])
    base = Path(where[0]) if where else Path(".")
    includes = find_cfg.get("include", [])
    if includes:
        candidates = [i for i in includes if "*" not in i and "." not in i]
        if candidates:
            pkg_name = min(candidates, key=len)
            pkg_path = base / pkg_name
            if pkg_path.is_dir() and (pkg_path / "__init__.py").exists():
                return pkg_path

    # Fallback: project name
    project_name = data.get("project", {}).get("name", "")
    if project_name:
        normalized = project_name.replace("-", "_").lower()
        pkg_path = base / normalized
        if pkg_path.is_dir() and (pkg_path / "__init__.py").exists():
            return pkg_path

    # Last resort: scan
    for d in sorted(Path(".").iterdir()):
        if d.is_dir() and d.name not in _SKIP_DIRS and not d.name.startswith("."):
            if (d / "__init__.py").exists():
                return d

    return None


def find_band_dirs(pkg_dir: Path) -> list[Path]:
    """Find band subdirectories within a multi-band PDK package.

    A band is a subdirectory that has __init__.py and (cells/ or tech.py).
    Returns an empty list for non-multi-band PDKs.
    """
    bands: list[Path] = []
    for d in sorted(pkg_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        if not (d / "__init__.py").exists():
            continue
        has_cells = (d / "cells").is_dir() or (d / "cells.py").exists()
        has_tech = (d / "tech.py").exists()
        if has_cells or has_tech:
            bands.append(d)
    return bands


def find_cell_files(pkg_dir: Path) -> list[Path]:
    """Find all Python cell files in the package.

    Searches cells/*.py and <band>/cells/*.py, excluding __init__.py.
    Also returns cells.py if it's a flat layout.
    """
    cell_files: list[Path] = []

    def _collect(base: Path) -> None:
        cells_dir = base / "cells"
        if cells_dir.is_dir():
            cell_files.extend(
                p for p in sorted(cells_dir.glob("*.py")) if p.name != "__init__.py"
            )
        elif (base / "cells.py").exists():
            cell_files.append(base / "cells.py")

    _collect(pkg_dir)
    for band_dir in find_band_dirs(pkg_dir):
        _collect(band_dir)

    return cell_files


def get_pdk_subdirs(pkg_dir: Path) -> list[Path]:
    """Return the list of directories to check for tech/cells/pdk structure.

    For a flat PDK, returns [pkg_dir].
    For a multi-band PDK, returns the band directories.
    """
    bands = find_band_dirs(pkg_dir)
    if bands:
        return bands
    return [pkg_dir]


# ── Reporting ────────────────────────────────────────────────────────


class CheckResult:
    """Accumulates pass/fail sub-check results for a hook."""

    def __init__(self, hook_name: str) -> None:
        self.hook_name = hook_name
        self._errors: list[str] = []
        self._warnings: list[str] = []

    def error(self, msg: str) -> None:
        """Record a failing check (causes hook to return 1)."""
        self._errors.append(msg)

    def warn(self, msg: str) -> None:
        """Record a non-fatal warning (printed but doesn't fail the hook)."""
        self._warnings.append(msg)

    @property
    def has_errors(self) -> bool:
        return bool(self._errors)

    def report(self) -> int:
        """Print results and return exit code (0=pass, 1=fail)."""
        if not self._errors and not self._warnings:
            return 0

        if self._errors:
            print(f"\n{'=' * 60}")
            print(f"  {self.hook_name}: {len(self._errors)} error(s) found")
            print(f"{'=' * 60}")
            for e in self._errors:
                print(f"  \u274c {e}")

        if self._warnings:
            if not self._errors:
                print()
            print(f"  Warnings:")
            for w in self._warnings:
                print(f"  \u26a0\ufe0f  {w}")

        print()
        return 1 if self._errors else 0


# ── AST helpers ──────────────────────────────────────────────────────


def parse_file(path: Path) -> ast.Module | None:
    """Parse a Python file, returning None on syntax errors."""
    try:
        return ast.parse(path.read_text(), filename=str(path))
    except SyntaxError:
        return None


def find_assignments(tree: ast.Module, name: str) -> list[ast.Assign]:
    """Find top-level assignments to a given name."""
    results: list[ast.Assign] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    results.append(node)
    return results


def get_assigned_string(tree: ast.Module, name: str) -> str | None:
    """Get the string value of a top-level assignment like __version__ = '1.0'."""
    for assign in find_assignments(tree, name):
        if isinstance(assign.value, ast.Constant) and isinstance(
            assign.value.value, str
        ):
            return assign.value.value
    return None


def has_if_name_main(tree: ast.Module) -> bool:
    """Check if module has ``if __name__ == '__main__':`` block."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            if _is_main_guard(node.test):
                return True
    return False


def _is_main_guard(test: ast.Compare) -> bool:
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False
    left, right = test.left, test.comparators[0]
    # __name__ == "__main__"
    if (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    ):
        return True
    # "__main__" == __name__
    if (
        isinstance(right, ast.Name)
        and right.id == "__name__"
        and isinstance(left, ast.Constant)
        and left.value == "__main__"
    ):
        return True
    return False


def get_import_aliases(tree: ast.Module) -> dict[str, str]:
    """Build a mapping of local names to their fully-qualified import paths.

    Examples:
        import gdsfactory as gf  ->  {'gf': 'gdsfactory'}
        from gdsfactory import cell  ->  {'cell': 'gdsfactory.cell'}
    """
    aliases: dict[str, str] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                aliases[local] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                aliases[local] = f"{module}.{alias.name}" if module else alias.name
    return aliases


def has_decorator(func_def: ast.FunctionDef, name: str) -> bool:
    """Check if a function has a @gf.cell-style decorator.

    Handles: @gf.cell, @cell, @gf.cell(), and import aliases.
    """
    for dec in func_def.decorator_list:
        # Unwrap Call: @gf.cell() or @cell()
        node = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(node, ast.Attribute):
            if node.attr == name:
                return True
        elif isinstance(node, ast.Name):
            if node.id == name:
                return True
    return False


def is_gf_cell_decorator(
    decorator: ast.expr, aliases: dict[str, str]
) -> bool:
    """Check if a decorator node represents @gf.cell (or equivalent)."""
    # Unwrap Call: @gf.cell() or @gf.cell(autoname=True)
    node = decorator.func if isinstance(decorator, ast.Call) else decorator

    if isinstance(node, ast.Attribute):
        # gf.cell -> check if gf resolves to gdsfactory
        if node.attr == "cell" and isinstance(node.value, ast.Name):
            resolved = aliases.get(node.value.id, node.value.id)
            if "gdsfactory" in resolved or node.value.id == "gf":
                return True
    elif isinstance(node, ast.Name):
        # cell or _cell -> check if it resolves to gdsfactory.cell
        resolved = aliases.get(node.id, "")
        if "gdsfactory" in resolved and "cell" in resolved:
            return True
        if node.id in ("cell", "_cell"):
            return True
    return False


def returns_component(
    func: ast.FunctionDef, aliases: dict[str, str]
) -> bool:
    """Check if function return annotation indicates gf.Component."""
    ann = func.returns
    if ann is None:
        return False
    if isinstance(ann, ast.Attribute):
        if ann.attr == "Component" and isinstance(ann.value, ast.Name):
            resolved = aliases.get(ann.value.id, ann.value.id)
            if "gdsfactory" in resolved or ann.value.id == "gf":
                return True
    elif isinstance(ann, ast.Name):
        resolved = aliases.get(ann.id, "")
        if "Component" in ann.id and "gdsfactory" in resolved:
            return True
    elif isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        if "Component" in ann.value:
            return True
    return False


def has_google_args_section(docstring: str) -> bool:
    """Check if docstring contains a Google-style 'Args:' section."""
    return bool(re.search(r"^\s*Args:\s*$", docstring, re.MULTILINE))


def get_docstring_from_node(node: ast.FunctionDef) -> str | None:
    """Extract the docstring from a function definition."""
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value
    return None
