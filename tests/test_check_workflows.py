"""Tests for check_workflows hook."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hooks.check_workflows import main


def _write_workflow(root: Path, name: str, data: dict[str, Any]) -> None:
    wf_dir = root / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / name).write_text(yaml.dump(data, default_flow_style=False))


class TestCheckWorkflows:
    def test_valid_workflow_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_missing_workflows_dir_fails(self, pdk_root: Path) -> None:
        import shutil

        shutil.rmtree(pdk_root / ".github" / "workflows")
        assert main() == 1

    def test_missing_test_code_yml_fails(self, pdk_root: Path) -> None:
        (pdk_root / ".github" / "workflows" / "test_code.yml").unlink()
        assert main() == 1

    def test_test_yml_alternative_accepted(self, pdk_root: Path) -> None:
        """test.yml should be accepted as an alternative."""
        tc = pdk_root / ".github" / "workflows" / "test_code.yml"
        tc.rename(tc.parent / "test.yml")
        assert main() == 0

    def test_no_precommit_job_fails(self, pdk_root: Path) -> None:
        _write_workflow(pdk_root, "test_code.yml", {
            "name": "Test",
            "on": {"push": None},
            "jobs": {
                "test_code": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"run": "make test"}],
                }
            },
        })
        assert main() == 1

    def test_centralized_workflow_passes(self, pdk_root: Path) -> None:
        """Delegating to pdk-ci-workflow test_code should pass."""
        _write_workflow(pdk_root, "test_code.yml", {
            "name": "Test",
            "on": {"push": None},
            "jobs": {
                "test": {
                    "uses": "org/pdk-ci-workflow/.github/workflows/test_code.yml@main",
                    "secrets": "inherit",
                }
            },
        })
        assert main() == 0

    def test_precommit_in_step_detected(self, pdk_root: Path) -> None:
        """Pre-commit used in a step (not job name) should be detected."""
        _write_workflow(pdk_root, "test_code.yml", {
            "name": "Test",
            "on": {"push": None},
            "jobs": {
                "lint": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {"uses": "pre-commit/action@v3"},
                    ],
                },
                "test_code": {
                    "runs-on": "ubuntu-latest",
                    "steps": [{"run": "make test"}],
                },
            },
        })
        assert main() == 0

    def test_missing_release_yml_warns(self, pdk_root: Path) -> None:
        """Missing release.yml should warn but not fail."""
        # Our fixture doesn't create release.yml, so this should just warn
        assert main() == 0

    def test_no_test_job_warns(self, pdk_root: Path) -> None:
        """Missing test job should warn but not fail."""
        _write_workflow(pdk_root, "test_code.yml", {
            "name": "Test",
            "on": {"push": None},
            "jobs": {
                "pre-commit": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {"uses": "pre-commit/action@v3"},
                    ],
                },
            },
        })
        # Should pass but with a warning about missing test job
        assert main() == 0
