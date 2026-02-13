"""Pre-commit hook: validate PDK package __init__.py structure."""

from __future__ import annotations

import sys

from hooks._utils import (
    CheckResult,
    find_assignments,
    find_package_dir,
    get_assigned_string,
    parse_file,
)


def main() -> int:
    result = CheckResult("check-package-init")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        result.warn("Could not find package directory — skipping.")
        return result.report()

    init_path = pkg_dir / "__init__.py"
    if not init_path.exists():
        result.error(f"{init_path} does not exist")
        return result.report()

    tree = parse_file(init_path)
    if tree is None:
        result.error(f"{init_path} has syntax errors")
        return result.report()

    # __version__ must be defined as a string literal
    version = get_assigned_string(tree, "__version__")
    if version is None:
        if find_assignments(tree, "__version__"):
            result.error(
                f"{init_path}: __version__ is defined but not as a string literal "
                '(must be __version__ = "X.Y.Z")'
            )
        else:
            result.error(f"{init_path}: __version__ is not defined")

    # __all__ must be defined
    if not find_assignments(tree, "__all__"):
        result.error(f"{init_path}: __all__ is not defined")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
