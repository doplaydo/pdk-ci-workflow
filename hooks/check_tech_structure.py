"""Pre-commit hook: validate PDK tech.py defines required technology objects."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from hooks._utils import CheckResult, find_package_dir, get_pdk_subdirs, parse_file

REQUIRED_NAMES = {"LAYER", "LAYER_STACK", "LAYER_VIEWS", "cross_sections"}
RECOMMENDED_NAMES = {"routing_strategies"}


def collect_defined_names(tree: ast.Module) -> dict[str, int]:
    """Collect all names defined or imported at module level, with line numbers."""
    found: dict[str, int] = {}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.lineno
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found[node.target.id] = node.lineno
        elif isinstance(node, ast.ClassDef):
            found[node.name] = node.lineno
        elif isinstance(node, ast.FunctionDef):
            found[node.name] = node.lineno
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                found[name] = node.lineno

    return found


def check_tech_file(tech_path: Path, result: CheckResult) -> None:
    """Validate a single tech.py file."""
    tree = parse_file(tech_path)
    if tree is None:
        result.error(f"{tech_path}: could not parse (syntax error)")
        return

    defined = collect_defined_names(tree)

    for name in REQUIRED_NAMES:
        if name not in defined:
            result.error(f"{tech_path}: required definition '{name}' not found")

    for name in RECOMMENDED_NAMES:
        if name not in defined:
            result.warn(f"{tech_path}: recommended definition '{name}' not found")


def check_layers_consistency(
    pkg_dir: Path, result: CheckResult
) -> None:
    """Cross-check layers.yaml with LAYER class if both exist."""
    yaml_path = None
    for candidate in [pkg_dir / "layers.yaml", pkg_dir / "layers.yml"]:
        if candidate.exists():
            yaml_path = candidate
            break

    if yaml_path is None:
        return

    # Parse layer names from YAML (top-level keys)
    yaml_layers: set[str] = set()
    content = yaml_path.read_text()
    for line in content.split("\n"):
        m = re.match(r"^(\w+)\s*:", line)
        if m:
            yaml_layers.add(m.group(1))

    # Parse LAYER class from layers.py or tech.py
    code_layers: set[str] = set()
    for src_name in ["layers.py", "tech.py"]:
        src_path = pkg_dir / src_name
        if not src_path.exists():
            continue
        tree = parse_file(src_path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "LAYER" in node.name.upper():
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(
                        item.target, ast.Name
                    ):
                        code_layers.add(item.target.id)
                    elif isinstance(item, ast.Assign):
                        for t in item.targets:
                            if isinstance(t, ast.Name):
                                code_layers.add(t.id)

    if not code_layers:
        return

    only_in_code = code_layers - yaml_layers
    only_in_yaml = yaml_layers - code_layers

    if only_in_code:
        result.warn(
            f"{yaml_path.parent}: layers in code but not in layers.yaml: "
            f"{sorted(only_in_code)}"
        )
    if only_in_yaml:
        result.warn(
            f"{yaml_path.parent}: layers in layers.yaml but not in code: "
            f"{sorted(only_in_yaml)}"
        )


def main() -> int:
    result = CheckResult("check-tech-structure")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        result.warn("Could not find package directory — skipping.")
        return result.report()

    subdirs = get_pdk_subdirs(pkg_dir)

    for subdir in subdirs:
        tech_path = subdir / "tech.py"
        if not tech_path.exists():
            result.error(f"{subdir}: tech.py not found")
            continue
        check_tech_file(tech_path, result)
        check_layers_consistency(subdir, result)

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
