"""Pre-commit hook: detect raw layer tuples in cell files."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from hooks._utils import CheckResult, find_cell_files, find_package_dir, parse_file

LAYER_SOURCE_FILES = {"tech.py", "layers.py", "config.py"}


class RawLayerTupleFinder(ast.NodeVisitor):
    """Find (int, int) tuples used as layer arguments in cell code."""

    def __init__(self, filepath: Path, result: CheckResult) -> None:
        self.filepath = filepath
        self.result = result
        self._in_default = False
        self._in_class_body = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Check parameter defaults — these are allowed (LayerSpec defaults)
        self._in_default = True
        for default in node.args.defaults + [
            d for d in node.args.kw_defaults if d is not None
        ]:
            self.visit(default)
        self._in_default = False

        # Visit function body
        for child in node.body:
            self.visit(child)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old = self._in_class_body
        self._in_class_body = True
        self.generic_visit(node)
        self._in_class_body = old

    def visit_Tuple(self, node: ast.Tuple) -> None:
        if self._in_default or self._in_class_body:
            self.generic_visit(node)
            return

        if self._is_layer_tuple(node):
            a, b = node.elts[0].value, node.elts[1].value  # type: ignore[union-attr]
            self.result.error(
                f"{self.filepath}:{node.lineno} raw layer tuple ({a}, {b}) — "
                f"use LAYER.XXX constant instead"
            )
        self.generic_visit(node)

    @staticmethod
    def _is_layer_tuple(node: ast.Tuple) -> bool:
        if len(node.elts) != 2:
            return False
        return all(
            isinstance(e, ast.Constant) and isinstance(e.value, int)
            for e in node.elts
        )


def main() -> int:
    result = CheckResult("check-no-raw-layers")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        return 0

    cell_files = find_cell_files(pkg_dir)

    for cell_file in cell_files:
        if cell_file.name in LAYER_SOURCE_FILES:
            continue

        tree = parse_file(cell_file)
        if tree is None:
            continue

        finder = RawLayerTupleFinder(cell_file, result)
        finder.visit(tree)

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
