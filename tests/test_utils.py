"""Tests for hooks._utils module."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hooks._utils import (
    CheckResult,
    find_assignments,
    find_band_dirs,
    find_cell_files,
    find_package_dir,
    get_assigned_string,
    get_docstring_from_node,
    get_import_aliases,
    has_decorator,
    has_google_args_section,
    has_if_name_main,
    is_gf_cell_decorator,
    parse_file,
    returns_component,
)


# ── CheckResult ──────────────────────────────────────────────────────


class TestCheckResult:
    def test_no_issues_returns_zero(self) -> None:
        cr = CheckResult("test")
        assert cr.report() == 0
        assert not cr.has_errors

    def test_error_returns_one(self) -> None:
        cr = CheckResult("test")
        cr.error("something broke")
        assert cr.has_errors
        assert cr.report() == 1

    def test_warning_only_returns_zero(self) -> None:
        cr = CheckResult("test")
        cr.warn("minor issue")
        assert not cr.has_errors
        # warnings print but don't fail
        assert cr.report() == 0


# ── parse_file ───────────────────────────────────────────────────────


class TestParseFile:
    def test_valid_python(self, tmp_path: Path) -> None:
        p = tmp_path / "good.py"
        p.write_text("x = 1\n")
        tree = parse_file(p)
        assert tree is not None

    def test_syntax_error_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text("def (:\n")
        assert parse_file(p) is None


# ── find_assignments / get_assigned_string ───────────────────────────


class TestAssignments:
    def test_find_simple_assignment(self) -> None:
        tree = ast.parse('__version__ = "1.0"\n')
        assigns = find_assignments(tree, "__version__")
        assert len(assigns) == 1

    def test_find_no_assignment(self) -> None:
        tree = ast.parse("x = 1\n")
        assert find_assignments(tree, "__version__") == []

    def test_get_assigned_string(self) -> None:
        tree = ast.parse('__version__ = "2.3.4"\n')
        assert get_assigned_string(tree, "__version__") == "2.3.4"

    def test_get_assigned_string_not_string(self) -> None:
        tree = ast.parse("__version__ = 42\n")
        assert get_assigned_string(tree, "__version__") is None

    @given(version=st.from_regex(r"[0-9]+\.[0-9]+\.[0-9]+", fullmatch=True))
    def test_get_assigned_string_semver(self, version: str) -> None:
        tree = ast.parse(f'__version__ = "{version}"\n')
        assert get_assigned_string(tree, "__version__") == version


# ── has_if_name_main ─────────────────────────────────────────────────


class TestHasIfNameMain:
    def test_detects_standard_guard(self) -> None:
        tree = ast.parse('if __name__ == "__main__":\n    pass\n')
        assert has_if_name_main(tree) is True

    def test_detects_reversed_guard(self) -> None:
        tree = ast.parse('if "__main__" == __name__:\n    pass\n')
        assert has_if_name_main(tree) is True

    def test_no_guard(self) -> None:
        tree = ast.parse("x = 1\n")
        assert has_if_name_main(tree) is False

    def test_different_comparison(self) -> None:
        tree = ast.parse('if __name__ != "__main__":\n    pass\n')
        assert has_if_name_main(tree) is False


# ── get_import_aliases ───────────────────────────────────────────────


class TestGetImportAliases:
    def test_import_as(self) -> None:
        tree = ast.parse("import gdsfactory as gf\n")
        aliases = get_import_aliases(tree)
        assert aliases["gf"] == "gdsfactory"

    def test_from_import(self) -> None:
        tree = ast.parse("from gdsfactory import cell\n")
        aliases = get_import_aliases(tree)
        assert aliases["cell"] == "gdsfactory.cell"

    def test_from_import_star_ignored(self) -> None:
        tree = ast.parse("from gdsfactory import *\n")
        aliases = get_import_aliases(tree)
        assert len(aliases) == 0


# ── is_gf_cell_decorator ────────────────────────────────────────────


class TestIsGfCellDecorator:
    def test_gf_dot_cell(self) -> None:
        tree = ast.parse("@gf.cell\ndef f(): pass\n")
        func = tree.body[0]
        aliases = {"gf": "gdsfactory"}
        assert is_gf_cell_decorator(func.decorator_list[0], aliases)

    def test_gf_dot_cell_call(self) -> None:
        tree = ast.parse("@gf.cell()\ndef f(): pass\n")
        func = tree.body[0]
        aliases = {"gf": "gdsfactory"}
        assert is_gf_cell_decorator(func.decorator_list[0], aliases)

    def test_bare_cell(self) -> None:
        tree = ast.parse("@cell\ndef f(): pass\n")
        func = tree.body[0]
        aliases = {"cell": "gdsfactory.cell"}
        assert is_gf_cell_decorator(func.decorator_list[0], aliases)

    def test_unrelated_decorator(self) -> None:
        tree = ast.parse("@property\ndef f(): pass\n")
        func = tree.body[0]
        aliases = {}
        assert not is_gf_cell_decorator(func.decorator_list[0], aliases)


# ── returns_component ────────────────────────────────────────────────


class TestReturnsComponent:
    def test_gf_component_annotation(self) -> None:
        tree = ast.parse("def f() -> gf.Component: pass\n")
        func = tree.body[0]
        aliases = {"gf": "gdsfactory"}
        assert returns_component(func, aliases)

    def test_no_annotation(self) -> None:
        tree = ast.parse("def f(): pass\n")
        func = tree.body[0]
        aliases = {}
        assert not returns_component(func, aliases)

    def test_string_annotation(self) -> None:
        tree = ast.parse('def f() -> "Component": pass\n')
        func = tree.body[0]
        aliases = {}
        assert returns_component(func, aliases)


# ── has_google_args_section ──────────────────────────────────────────


class TestHasGoogleArgsSection:
    def test_has_args(self) -> None:
        doc = "Summary.\n\nArgs:\n    x: the value.\n"
        assert has_google_args_section(doc) is True

    def test_no_args(self) -> None:
        doc = "Summary only.\n"
        assert has_google_args_section(doc) is False

    def test_args_inline_not_matched(self) -> None:
        # "Args:" must be on its own line
        doc = "Summary with Args: embedded.\n"
        assert has_google_args_section(doc) is False


# ── get_docstring_from_node ──────────────────────────────────────────


class TestGetDocstringFromNode:
    def test_has_docstring(self) -> None:
        tree = ast.parse('def f():\n    """Hello."""\n    pass\n')
        func = tree.body[0]
        assert get_docstring_from_node(func) == "Hello."

    def test_no_docstring(self) -> None:
        tree = ast.parse("def f():\n    pass\n")
        func = tree.body[0]
        assert get_docstring_from_node(func) is None


# ── find_package_dir ─────────────────────────────────────────────────


class TestFindPackageDir:
    def test_from_setuptools_include(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [project]
                name = "my-pdk"
                [tool.setuptools.packages.find]
                include = ["my_pdk"]
            """)
        )
        pkg = tmp_path / "my_pdk"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        result = find_package_dir()
        assert result is not None
        assert result.resolve() == pkg.resolve()

    def test_fallback_project_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "my-pdk"\n'
        )
        pkg = tmp_path / "my_pdk"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        result = find_package_dir()
        assert result is not None
        assert result.resolve() == pkg.resolve()

    def test_scan_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'unrelated'\n")
        pkg = tmp_path / "alpha_pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        result = find_package_dir()
        assert result is not None
        assert result.resolve() == pkg.resolve()

    def test_no_pyproject(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert find_package_dir() is None


# ── find_band_dirs ───────────────────────────────────────────────────


class TestFindBandDirs:
    def test_single_band(self, tmp_path: Path) -> None:
        band = tmp_path / "c_band"
        band.mkdir()
        (band / "__init__.py").write_text("")
        (band / "tech.py").write_text("")
        assert find_band_dirs(tmp_path) == [band]

    def test_ignores_private_dirs(self, tmp_path: Path) -> None:
        band = tmp_path / "_internal"
        band.mkdir()
        (band / "__init__.py").write_text("")
        (band / "tech.py").write_text("")
        assert find_band_dirs(tmp_path) == []

    def test_no_tech_no_cells(self, tmp_path: Path) -> None:
        sub = tmp_path / "utils"
        sub.mkdir()
        (sub / "__init__.py").write_text("")
        assert find_band_dirs(tmp_path) == []


# ── find_cell_files ──────────────────────────────────────────────────


class TestFindCellFiles:
    def test_cells_directory(self, tmp_path: Path) -> None:
        cells = tmp_path / "cells"
        cells.mkdir()
        (cells / "__init__.py").write_text("")
        (cells / "waveguides.py").write_text("")
        (cells / "couplers.py").write_text("")
        result = find_cell_files(tmp_path)
        names = [p.name for p in result]
        assert "waveguides.py" in names
        assert "couplers.py" in names
        assert "__init__.py" not in names

    def test_cells_py_flat(self, tmp_path: Path) -> None:
        (tmp_path / "cells.py").write_text("")
        result = find_cell_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "cells.py"
