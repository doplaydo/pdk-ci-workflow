"""Tests for check_pyproject_sections hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hooks.check_pyproject_sections import main


class TestCheckPyprojectSections:
    def test_valid_pyproject_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_no_pyproject_skips(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main() == 0

    def test_missing_build_system_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        # Remove the [build-system] section
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if line.strip() == "[build-system]":
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_missing_project_section_fails(self, pdk_root: Path) -> None:
        (pdk_root / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [build-system]
                requires = ["setuptools"]
                build-backend = "setuptools.build_meta"
            """)
        )
        assert main() == 1

    def test_missing_project_name_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace('name = "my-pdk"', "")
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_missing_project_version_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        # Remove project version (but not tbump version)
        lines = content.split("\n")
        new_lines = []
        in_project = False
        for line in lines:
            if line.strip() == "[project]":
                in_project = True
            elif line.startswith("[") and in_project:
                in_project = False
            if in_project and line.strip().startswith("version"):
                continue
            new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_wrong_readme_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace('readme = "README.md"', 'readme = "readme.rst"')
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_missing_gdsfactory_dep_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace(
            'dependencies = ["gdsfactory>=7.0"]',
            'dependencies = ["numpy"]',
        )
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_wrong_license_format_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace(
            'license = {file = "LICENSE"}',
            'license = "MIT"',
        )
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_missing_ruff_section_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        # Remove all ruff sections
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "[tool.ruff" in line:
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_ruff_select_at_wrong_level_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        # Add select at [tool.ruff] level (not [tool.ruff.lint])
        content = content.replace(
            "[tool.ruff]\nfix = true",
            '[tool.ruff]\nfix = true\nselect = ["E"]',
        )
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_missing_codespell_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "[tool.codespell]" in line:
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_missing_pytest_section_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "[tool.pytest" in line:
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_missing_package_data_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "[tool.setuptools.package-data]" in line:
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_missing_tbump_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "tool.tbump" in line:
                skip = True
                continue
            if skip and line.startswith("[") and "tbump" not in line:
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_missing_mypy_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "[tool.mypy]" in line:
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        assert main() == 1

    def test_missing_keywords_python_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace(
            'keywords = ["python", "photonics"]',
            'keywords = ["photonics"]',
        )
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_missing_authors_fails(self, pdk_root: Path) -> None:
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace(
            'authors = [{name = "Test Author"}]',
            "authors = []",
        )
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 1

    def test_missing_towncrier_only_warns(self, pdk_root: Path) -> None:
        """Towncrier is recommended, not required."""
        content = (pdk_root / "pyproject.toml").read_text()
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "[tool.towncrier]" in line:
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                new_lines.append(line)
        (pdk_root / "pyproject.toml").write_text("\n".join(new_lines))
        # Should pass (towncrier is warn-only)
        assert main() == 0
