"""Tests for check_precommit_config hook."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hooks.check_precommit_config import main


def _write_config(root: Path, config: dict[str, Any]) -> None:
    (root / ".pre-commit-config.yaml").write_text(
        yaml.dump(config, default_flow_style=False)
    )


class TestCheckPrecommitConfig:
    def test_valid_config_passes(self, pdk_root: Path) -> None:
        assert main() == 0

    def test_missing_config_fails(self, pdk_root: Path) -> None:
        (pdk_root / ".pre-commit-config.yaml").unlink()
        assert main() == 1

    def test_missing_eof_fixer_fails(self, pdk_root: Path) -> None:
        _write_config(pdk_root, {
            "repos": [{
                "repo": "local",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "ruff-format"},
                    {"id": "ruff-lint"},
                ],
            }]
        })
        assert main() == 1

    def test_missing_trailing_whitespace_fails(self, pdk_root: Path) -> None:
        _write_config(pdk_root, {
            "repos": [{
                "repo": "local",
                "hooks": [
                    {"id": "end-of-file-fixer"},
                    {"id": "ruff-format"},
                    {"id": "ruff-lint"},
                ],
            }]
        })
        assert main() == 1

    def test_missing_ruff_format_fails(self, pdk_root: Path) -> None:
        _write_config(pdk_root, {
            "repos": [{
                "repo": "local",
                "hooks": [
                    {"id": "end-of-file-fixer"},
                    {"id": "trailing-whitespace"},
                    {"id": "ruff-lint"},
                ],
            }]
        })
        assert main() == 1

    def test_ruff_or_ruff_lint_required(self, pdk_root: Path) -> None:
        """Must have either 'ruff' or 'ruff-lint'."""
        _write_config(pdk_root, {
            "repos": [{
                "repo": "local",
                "hooks": [
                    {"id": "end-of-file-fixer"},
                    {"id": "trailing-whitespace"},
                    {"id": "ruff-format"},
                ],
            }]
        })
        assert main() == 1

    def test_old_ruff_id_accepted(self, pdk_root: Path) -> None:
        """The old 'ruff' hook ID should also satisfy the requirement."""
        _write_config(pdk_root, {
            "repos": [{
                "repo": "local",
                "hooks": [
                    {"id": "end-of-file-fixer"},
                    {"id": "trailing-whitespace"},
                    {"id": "ruff-format"},
                    {"id": "ruff"},
                ],
            }]
        })
        assert main() == 0

    def test_missing_recommended_only_warns(self, pdk_root: Path) -> None:
        """Missing nbstripout/codespell should not fail."""
        _write_config(pdk_root, {
            "repos": [{
                "repo": "local",
                "hooks": [
                    {"id": "end-of-file-fixer"},
                    {"id": "trailing-whitespace"},
                    {"id": "ruff-format"},
                    {"id": "ruff-lint"},
                ],
            }]
        })
        assert main() == 0

    def test_hooks_across_multiple_repos(self, pdk_root: Path) -> None:
        """Hook IDs should be collected across all repos."""
        _write_config(pdk_root, {
            "repos": [
                {
                    "repo": "https://github.com/pre-commit/pre-commit-hooks",
                    "rev": "v4.5.0",
                    "hooks": [
                        {"id": "end-of-file-fixer"},
                        {"id": "trailing-whitespace"},
                    ],
                },
                {
                    "repo": "https://github.com/astral-sh/ruff-pre-commit",
                    "rev": "v0.3.0",
                    "hooks": [
                        {"id": "ruff-format"},
                        {"id": "ruff"},
                    ],
                },
            ]
        })
        assert main() == 0

    def test_empty_repos_fails(self, pdk_root: Path) -> None:
        """No repos means no hooks — all required hooks missing."""
        _write_config(pdk_root, {"repos": []})
        assert main() == 1
