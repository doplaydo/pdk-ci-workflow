"""Pre-commit hook: validate Pdk() constructor has required fields and uses get_cells()."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from hooks._utils import (
    CheckResult,
    find_package_dir,
    get_import_aliases,
    get_pdk_subdirs,
    parse_file,
)

REQUIRED_KWARGS = {"name", "cells", "layers", "cross_sections"}
RECOMMENDED_KWARGS = {"layer_views", "layer_stack", "routing_strategies"}


def _find_get_cells_vars(tree: ast.Module) -> set[str]:
    """Find variable names assigned from get_cells() calls at module level.

    Matches patterns like: _cells = get_cells(cells)
    """
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            is_get_cells = (
                (isinstance(func, ast.Name) and func.id == "get_cells")
                or (isinstance(func, ast.Attribute) and func.attr == "get_cells")
            )
            if is_get_cells:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
    return names


class PdkCallChecker(ast.NodeVisitor):
    """Find and validate Pdk() constructor calls."""

    def __init__(
        self,
        filepath: Path,
        aliases: dict[str, str],
        result: CheckResult,
        get_cells_vars: set[str],
    ) -> None:
        self.filepath = filepath
        self.aliases = aliases
        self.result = result
        self.found_pdk_call = False
        self._get_cells_vars = get_cells_vars

    def visit_Call(self, node: ast.Call) -> None:
        if not self._is_pdk_constructor(node.func):
            self.generic_visit(node)
            return

        self.found_pdk_call = True

        # Collect keyword argument names
        kwarg_names = {kw.arg for kw in node.keywords if kw.arg is not None}

        # Check required kwargs
        missing = REQUIRED_KWARGS - kwarg_names
        if missing:
            self.result.error(
                f"{self.filepath}:{node.lineno} Pdk() missing required kwargs: "
                f"{sorted(missing)}"
            )

        # Check recommended kwargs
        missing_rec = RECOMMENDED_KWARGS - kwarg_names
        if missing_rec:
            self.result.warn(
                f"{self.filepath}:{node.lineno} Pdk() missing recommended kwargs: "
                f"{sorted(missing_rec)}"
            )

        # Check cells= uses get_cells() pattern
        for kw in node.keywords:
            if kw.arg == "cells" and not self._is_get_cells_value(kw.value):
                self.result.warn(
                    f"{self.filepath}:{node.lineno} Pdk(cells=...) should use "
                    f"get_cells() for dynamic cell discovery"
                )

        self.generic_visit(node)

    def _is_pdk_constructor(self, func_node: ast.expr) -> bool:
        if isinstance(func_node, ast.Name):
            resolved = self.aliases.get(func_node.id, func_node.id)
            return func_node.id == "Pdk" or "Pdk" in resolved
        elif isinstance(func_node, ast.Attribute):
            return func_node.attr == "Pdk"
        return False

    def _is_get_cells_value(self, value_node: ast.expr) -> bool:
        """Check if value is get_cells() call or a variable assigned from it."""
        # Direct call: get_cells(cells)
        if isinstance(value_node, ast.Call):
            func = value_node.func
            if isinstance(func, ast.Name) and func.id == "get_cells":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "get_cells":
                return True
        # Variable reference: _cells (previously assigned from get_cells)
        if isinstance(value_node, ast.Name):
            return value_node.id in self._get_cells_vars
        return False


def main() -> int:
    result = CheckResult("check-pdk-object")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        result.warn("Could not find package directory — skipping.")
        return result.report()

    found_any_pdk = False
    subdirs = get_pdk_subdirs(pkg_dir)

    for subdir in subdirs:
        # Search __init__.py and all .py files in the subdir
        candidates = [subdir / "__init__.py"]
        candidates.extend(sorted(subdir.glob("*.py")))

        # Also check pdk/ subdirectory (common pattern)
        pdk_subdir = subdir / "pdk"
        if pdk_subdir.is_dir():
            candidates.extend(sorted(pdk_subdir.glob("*.py")))

        seen: set[Path] = set()
        for filepath in candidates:
            if not filepath.exists() or filepath in seen:
                continue
            seen.add(filepath)

            tree = parse_file(filepath)
            if tree is None:
                continue

            aliases = get_import_aliases(tree)
            get_cells_vars = _find_get_cells_vars(tree)
            checker = PdkCallChecker(filepath, aliases, result, get_cells_vars)
            checker.visit(tree)
            if checker.found_pdk_call:
                found_any_pdk = True

    if not found_any_pdk:
        result.error("No Pdk() constructor call found in any package file")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
