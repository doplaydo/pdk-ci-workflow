"""Tests for check_package_init hook."""

from __future__ import annotations

from pathlib import Path

from hooks.check_package_init import main


class TestCheckPackageInit:
    def test_valid_init_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_missing_init_warns(self, pdk_root: Path) -> None:
        """When __init__.py is missing, find_package_dir fails and the hook
        warns + skips (returns 0).  This is expected: find_package_dir
        requires __init__.py to identify a package."""
        (pdk_root / "my_pdk" / "__init__.py").unlink()
        assert main() == 0

    def test_missing_version_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "__init__.py").write_text(
            '__all__ = ["cells"]\n'
        )
        assert main() == 1

    def test_version_not_string_literal_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "__init__.py").write_text(
            '__version__ = 1\n__all__ = ["cells"]\n'
        )
        assert main() == 1

    def test_missing_all_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "__init__.py").write_text(
            '__version__ = "0.1.0"\n'
        )
        assert main() == 1

    def test_syntax_error_fails(self, pdk_root: Path) -> None:
        (pdk_root / "my_pdk" / "__init__.py").write_text("def (:\n")
        assert main() == 1

    def test_version_as_expression_fails(self, pdk_root: Path) -> None:
        """__version__ assigned from a function call is not a string literal."""
        (pdk_root / "my_pdk" / "__init__.py").write_text(
            'from importlib.metadata import version\n'
            '__version__ = version("my-pdk")\n'
            '__all__ = ["cells"]\n'
        )
        assert main() == 1
