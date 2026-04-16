"""Tests for check_template_drift hook."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from hooks.check_template_drift import main


class TestCheckTemplateDrift:
    def test_self_repo_skips(self, pdk_root: Path) -> None:
        """Running inside pdk-ci-workflow itself should skip."""
        # The fixture's pyproject.toml uses name="my-pdk".
        # Override to the self-repo name.
        content = (pdk_root / "pyproject.toml").read_text()
        content = content.replace('name = "my-pdk"', 'name = "ci-pdk-workflows"')
        (pdk_root / "pyproject.toml").write_text(content)
        assert main() == 0

    def test_no_local_files_passes(self, pdk_root: Path) -> None:
        """If none of the template files exist locally, hook passes."""
        # Remove all .github files
        import shutil

        shutil.rmtree(pdk_root / ".github")
        assert main() == 0

    def test_matching_template_passes(self, pdk_root: Path) -> None:
        """If local file matches the template exactly, hook passes."""
        # We need to check if there's a template file that matches
        # The hook reads templates from importlib.resources
        # If the local file matches the shipped template, it should pass
        # Since our test repo files won't match the real templates,
        # let's mock the template content to match the local content
        from importlib.resources import files

        root = files("templates")

        # For each template file that exists locally, write its content
        from hooks.check_template_drift import TEMPLATES

        for rel in TEMPLATES:
            local = pdk_root / rel
            if not local.exists():
                continue
            parts = rel.split("/")
            src = root
            for p in parts:
                src = src.joinpath(p)
            if src.is_file():
                # Write template content to local file
                local.write_text(src.read_text(encoding="utf-8"))

        assert main() == 0

    def test_drifted_file_gets_rewritten(self, pdk_root: Path) -> None:
        """A drifted file should be rewritten and hook should return 1."""
        from importlib.resources import files

        from hooks.check_template_drift import TEMPLATES

        root = files("templates")

        # Find a template file that exists
        for rel in TEMPLATES:
            parts = rel.split("/")
            src = root
            for p in parts:
                src = src.joinpath(p)
            if src.is_file():
                # Create local file with different content
                local = pdk_root / rel
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_text("# this content is different\n")

                result = main()
                assert result == 1
                # After rewrite, local file should match template
                assert local.read_text() == src.read_text(encoding="utf-8")
                return

        pytest.skip("No template files found in package")

    def test_second_run_after_rewrite_passes(self, pdk_root: Path) -> None:
        """After rewriting, a second run should pass (Ruff-style auto-fix)."""
        from importlib.resources import files

        from hooks.check_template_drift import TEMPLATES

        root = files("templates")

        for rel in TEMPLATES:
            parts = rel.split("/")
            src = root
            for p in parts:
                src = src.joinpath(p)
            if src.is_file():
                local = pdk_root / rel
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_text("# drifted content\n")

                # First run: rewrite
                assert main() == 1
                # Second run: should pass
                assert main() == 0
                return

        pytest.skip("No template files found in package")
