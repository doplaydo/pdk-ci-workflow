"""Pre-commit hook: detect raw layer tuples in cell files."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from hooks._utils import CheckResult, find_cell_files, find_package_dir, parse_file

LAYER_SOURCE_FILES = {"tech.py", "layers.py", "config.py"}

# Keyword argument names that carry layer specs — (int, int) tuples here are raw layers
_LAYER_KWARG_NAMES: frozenset[str] = frozenset(
    {
        "layer",
        "layers",
        "layer_slab",
        "layer_pin",
        "layer_label",
        "layer_heater",
        "layer_trench",
        "layer_port",
        "layer_metal",
        "layer_via",
        "layers_via_stack1",
        "layers_via_stack2",
        "bbox_layers",
        "cladding_layers",
        "label_layer",
    }
)


class RawLayerTupleFinder(ast.NodeVisitor):
    """Find (int, int) tuples used as layer arguments in cell code."""

    def __init__(self, filepath: Path, result: CheckResult) -> None:
        self.filepath = filepath
        self.result = result
        self._in_default = False
        self._in_class_body = False
        # Current keyword argument name, or None when not inside a keyword argument.
        # Distinguishes layer kwargs (layer=, layers=, bbox_layers=, …) from
        # non-layer kwargs (center=, size=, offsets=, …).
        self._kwarg_name: str | None = None

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

    def visit_Call(self, node: ast.Call) -> None:
        # Visit positional args with current kwarg context unchanged
        for arg in node.args:
            self.visit(arg)

        # Visit each keyword arg, tracking the kwarg name so visit_Tuple can
        # distinguish layer kwargs from non-layer kwargs (size=, center=, …).
        for kw in node.keywords:
            old = self._kwarg_name
            self._kwarg_name = kw.arg  # None for **kwargs unpacking
            self.visit(kw.value)
            self._kwarg_name = old

    def visit_Tuple(self, node: ast.Tuple) -> None:
        if self._in_default or self._in_class_body:
            self.generic_visit(node)
            return

        if self._is_layer_tuple(node) and self._is_layer_context():
            a, b = node.elts[0].value, node.elts[1].value  # type: ignore[union-attr]
            self.result.error(
                f"{self.filepath}:{node.lineno} raw layer tuple ({a}, {b}) — "
                f"use LAYER.XXX constant instead"
            )
        self.generic_visit(node)

    def _is_layer_context(self) -> bool:
        """Return True if the current kwarg context looks like a layer argument."""
        if self._kwarg_name is None:
            # Not inside a keyword argument at all — flag conservatively.
            return True
        kwarg = self._kwarg_name
        return (
            kwarg in _LAYER_KWARG_NAMES
            or kwarg.endswith("_layer")
            or kwarg.endswith("_layers")
        )

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
