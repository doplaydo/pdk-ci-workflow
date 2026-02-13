"""Pre-commit hook: ensure cell files have no ``if __name__ == '__main__'`` blocks."""

from __future__ import annotations

import sys

from hooks._utils import (
    CheckResult,
    find_cell_files,
    find_package_dir,
    has_if_name_main,
    parse_file,
)


def main() -> int:
    result = CheckResult("check-no-main-in-cells")

    pkg_dir = find_package_dir()
    if pkg_dir is None:
        return 0

    for cell_file in find_cell_files(pkg_dir):
        tree = parse_file(cell_file)
        if tree is None:
            continue
        if has_if_name_main(tree):
            result.error(
                f'{cell_file}: contains `if __name__ == "__main__"` block — '
                f"remove debug/test code from cell files"
            )

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
