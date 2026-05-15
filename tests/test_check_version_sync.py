"""Tests for check_version_sync hook."""

from __future__ import annotations

import textwrap
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from hooks.check_version_sync import main


def _set_versions(
    root: Path,
    project_version: str = "0.1.0",
    tbump_version: str | None = None,
    init_version: str | None = None,
    readme_version: str | None = None,
) -> None:
    """Set version strings across the repo.  tbump/init/readme default to
    matching project_version when None."""
    tbump_version = tbump_version or project_version
    init_version = init_version or project_version
    readme_version = readme_version or project_version

    pyproject = textwrap.dedent(f"""\
        [project]
        name = "my-pdk"
        version = "{project_version}"

        [tool.setuptools.packages.find]
        include = ["my_pdk"]

        [tool.tbump.version]
        current = "{tbump_version}"
    """)
    (root / "pyproject.toml").write_text(pyproject)

    (root / "my_pdk" / "__init__.py").write_text(
        f'__version__ = "{init_version}"\n__all__ = ["cells"]\n'
    )

    (root / "README.md").write_text(
        f"# My PDK\npip install my-pdk=={readme_version}\n"
    )


class TestCheckVersionSync:
    def test_all_versions_match_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_project_vs_tbump_mismatch_fails(self, pdk_root: Path) -> None:
        _set_versions(
            pdk_root,
            project_version="0.1.0",
            tbump_version="0.2.0",
        )
        assert main() == 1

    def test_init_mismatch_fails(self, pdk_root: Path) -> None:
        _set_versions(
            pdk_root,
            project_version="0.1.0",
            init_version="0.9.9",
        )
        assert main() == 1

    def test_readme_mismatch_fails(self, pdk_root: Path) -> None:
        _set_versions(
            pdk_root,
            project_version="0.1.0",
            readme_version="0.2.0",
        )
        assert main() == 1

    def test_all_four_match_passes(self, pdk_root: Path) -> None:
        _set_versions(pdk_root, project_version="1.2.3")
        assert main() == 0

    def test_no_pyproject_warns_only(
        self, tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
    ) -> None:
        """Missing pyproject.toml should warn but not error."""
        monkeypatch.chdir(tmp_path)
        assert main() == 0

    @given(
        version=st.from_regex(
            r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", fullmatch=True
        )
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_consistent_version_always_passes(
        self, pdk_root: Path, version: str
    ) -> None:
        """Any consistent semver version across all locations should pass."""
        _set_versions(pdk_root, project_version=version)
        assert main() == 0

    @given(
        v1=st.from_regex(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}", fullmatch=True),
        v2=st.from_regex(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}", fullmatch=True),
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_versions_detected(
        self, pdk_root: Path, v1: str, v2: str
    ) -> None:
        """Two different version strings should be detected as a mismatch."""
        from hypothesis import assume

        assume(v1 != v2)
        _set_versions(pdk_root, project_version=v1, init_version=v2)
        assert main() == 1
