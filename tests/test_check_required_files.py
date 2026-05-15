"""Tests for check_required_files hook."""

from __future__ import annotations

from pathlib import Path

from hooks.check_required_files import main


class TestCheckRequiredFiles:
    """Verify the hook detects missing files (true positives) and passes
    for a valid repo (no false positives)."""

    def test_valid_repo_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_missing_readme(self, pdk_root: Path) -> None:
        (pdk_root / "README.md").unlink()
        assert main() == 1

    def test_missing_changelog(self, pdk_root: Path) -> None:
        (pdk_root / "CHANGELOG.md").unlink()
        assert main() == 1

    def test_missing_license(self, pdk_root: Path) -> None:
        (pdk_root / "LICENSE").unlink()
        assert main() == 1

    def test_missing_makefile(self, pdk_root: Path) -> None:
        (pdk_root / "Makefile").unlink()
        assert main() == 1

    def test_missing_pyproject(self, pdk_root: Path) -> None:
        (pdk_root / "pyproject.toml").unlink()
        assert main() == 1

    def test_missing_gitignore(self, pdk_root: Path) -> None:
        (pdk_root / ".gitignore").unlink()
        assert main() == 1

    def test_missing_precommit_config(self, pdk_root: Path) -> None:
        (pdk_root / ".pre-commit-config.yaml").unlink()
        assert main() == 1

    def test_missing_tests_dir(self, pdk_root: Path) -> None:
        import shutil

        shutil.rmtree(pdk_root / "tests")
        assert main() == 1

    def test_missing_release_drafter_workflow(self, pdk_root: Path) -> None:
        (pdk_root / ".github" / "workflows" / "release-drafter.yml").unlink()
        assert main() == 1

    def test_test_yml_alternative_accepted(self, pdk_root: Path) -> None:
        """test.yml should be accepted as an alternative to test_code.yml."""
        tc = pdk_root / ".github" / "workflows" / "test_code.yml"
        tc.rename(tc.parent / "test.yml")
        assert main() == 0

    def test_missing_both_test_workflows(self, pdk_root: Path) -> None:
        (pdk_root / ".github" / "workflows" / "test_code.yml").unlink()
        # Neither test_code.yml nor test.yml exists
        assert main() == 1

    def test_recommended_missing_is_warning_not_error(
        self, pdk_root: Path
    ) -> None:
        """Missing recommended files should not cause a failure."""
        # .gitattributes, .changelog.d/changelog_template.jinja, release.yml
        # are recommended. Remove changelog template (which we create in fixture)
        (pdk_root / ".changelog.d" / "changelog_template.jinja").unlink()
        # Hook should still pass (warnings only)
        assert main() == 0
