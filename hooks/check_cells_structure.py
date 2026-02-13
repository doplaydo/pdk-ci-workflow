"""Pre-commit hook: validate PDK cell functions have @gf.cell, docstrings, and re-exports."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from hooks._utils import (
    CheckResult,
    find_cell_files,
    find_package_dir,
    get_docstring_from_node,
    get_import_aliases,
    get_pdk_subdirs,
    has_google_args_section,
    is_gf_cell_decorator,
    parse_file,
    returns_component,
)


def check_cell_file(
    path: Path, aliases: dict[str, str], tree: ast.Module, result: CheckResult
) -> list[str]:
    """Check a single cell file. Returns list of @gf.cell function names found."""
    cell_func_names: list[str] = []

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        # Skip private functions
        if node.name.startswith("_"):
            continue

        has_cell_dec = any(
            is_gf_cell_decorator(d, aliases) for d in node.decorator_list
        )

        if has_cell_dec:
            cell_func_names.append(node.name)

            # Check docstring
            docstring = get_docstring_from_node(node)
            if docstring is None:
                result.error(
                    f"{path}:{node.lineno} @gf.cell function '{node.name}' "
                    f"missing docstring"
                )
            else:
                # Only require Args section if function has parameters
                params = [
                    a.arg for a in node.args.args if a.arg != "self"
                ]
                if params and not has_google_args_section(docstring):
                    result.error(
                        f"{path}:{node.lineno} @gf.cell function '{node.name}' "
                        f"docstring missing 'Args:' section"
                    )

        elif returns_component(node, aliases):
            # Returns Component but missing @gf.cell
            result.error(
                f"{path}:{node.lineno} function '{node.name}' returns Component "
                f"but missing @gf.cell decorator"
            )

    return cell_func_names


def check_cells_init_exports(
    cells_init: Path, cell_files: list[Path], result: CheckResult
) -> None:
    """Check that cells/__init__.py re-exports all cell modules."""
    tree = parse_file(cells_init)
    if tree is None:
        return

    exported_modules: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            # from .waveguides import * OR from .waveguides import ring_single
            if node.level >= 1:
                exported_modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                exported_modules.add(alias.name.split(".")[-1])

    for cell_file in cell_files:
        module_name = cell_file.stem
        if module_name not in exported_modules:
            result.error(
                f"{cells_init}: cell module '{module_name}' is not re-exported "
                f"(missing import from .{module_name})"
            )


def main() -> int:
    result = CheckResult("check-cells-structure")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        result.warn("Could not find package directory — skipping.")
        return result.report()

    subdirs = get_pdk_subdirs(pkg_dir)

    for subdir in subdirs:
        cells_dir = subdir / "cells"
        cells_py = subdir / "cells.py"

        if cells_dir.is_dir():
            cell_files = [
                p
                for p in sorted(cells_dir.glob("*.py"))
                if p.name != "__init__.py"
            ]

            for cell_file in cell_files:
                tree = parse_file(cell_file)
                if tree is None:
                    result.warn(f"{cell_file}: could not parse (syntax error)")
                    continue
                aliases = get_import_aliases(tree)
                check_cell_file(cell_file, aliases, tree, result)

            # Check cells/__init__.py re-exports
            cells_init = cells_dir / "__init__.py"
            if cells_init.exists() and cell_files:
                check_cells_init_exports(cells_init, cell_files, result)

        elif cells_py.exists():
            tree = parse_file(cells_py)
            if tree is None:
                result.warn(f"{cells_py}: could not parse (syntax error)")
            else:
                aliases = get_import_aliases(tree)
                check_cell_file(cells_py, aliases, tree, result)

        else:
            result.error(
                f"{subdir}: no cells module found (expected cells/ or cells.py)"
            )

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
