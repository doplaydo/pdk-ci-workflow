"""Tests for check_template_drift hook."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

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

    def test_no_local_files_fails_and_creates_them(self, pdk_root: Path) -> None:
        """If none of the template files exist locally, hook fails and creates them."""
        # Remove all .github files
        import shutil

        if (pdk_root / ".github").exists():
            shutil.rmtree(pdk_root / ".github")
        
        # Should fail because it creates them
        assert main() == 1
        
        # Verify at least one was created
        from hooks.check_template_drift import TEMPLATES
        assert (pdk_root / TEMPLATES[0]).exists()

    def test_matching_template_passes(self, pdk_root: Path) -> None:
        """If local file matches the template exactly, hook passes."""
        from importlib.resources import files
        from hooks.check_template_drift import TEMPLATES

        root = files("templates")

        # Ensure ALL template files exist locally and match the template
        for rel in TEMPLATES:
            local = pdk_root / rel
            local.parent.mkdir(parents=True, exist_ok=True)
            
            parts = rel.split("/")
            src = root
            for p in parts:
                src = src.joinpath(p)
            
            if src.is_file():
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

                # Note: other files in TEMPLATES might still be missing in pdk_root
                # and would also cause failure. But that's fine, result should be 1.
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
        
        # To ensure the second run passes, we must handle ALL templates
        for rel in TEMPLATES:
            local = pdk_root / rel
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text("# drifted content\n")

        # First run: rewrite (should return 1 because many files are "fixed")
        assert main() == 1
        # Second run: should pass (all match now)
        assert main() == 0
