"""Pre-commit hook: validate .pre-commit-config.yaml has required hooks."""

from __future__ import annotations

import sys

from hooks._utils import CheckResult, load_yaml

# Each hook ID must be present in at least one repo.
REQUIRED_HOOK_IDS: set[str] = {
    "end-of-file-fixer",
    "trailing-whitespace",
    "ruff-format",
}

# At least one ID from each set must be present (handles old/new configs).
REQUIRED_HOOK_IDS_ANY: list[set[str]] = [
    {"ruff", "ruff-lint"},  # old: ruff (from ruff-pre-commit), new: ruff-lint (wrapper)
]

RECOMMENDED_HOOK_IDS: set[str] = {"nbstripout", "codespell"}


def main() -> int:
    result = CheckResult("check-precommit-config")

    data = load_yaml(".pre-commit-config.yaml")
    if data is None:
        result.error(".pre-commit-config.yaml missing or could not be parsed")
        return result.report()

    # Collect all hook IDs across all repos
    all_hook_ids: set[str] = set()
    for repo in data.get("repos", []):
        if not isinstance(repo, dict):
            continue
        for hook in repo.get("hooks", []):
            if isinstance(hook, dict) and hook.get("id"):
                all_hook_ids.add(hook["id"])

    # Check required hooks
    for hook_id in REQUIRED_HOOK_IDS:
        if hook_id not in all_hook_ids:
            result.error(f"Missing required hook: {hook_id}")

    for alternatives in REQUIRED_HOOK_IDS_ANY:
        if not alternatives & all_hook_ids:
            names = " or ".join(sorted(alternatives))
            result.error(f"Missing required hook: {names}")

    # Check recommended hooks
    for hook_id in RECOMMENDED_HOOK_IDS:
        if hook_id not in all_hook_ids:
            result.warn(f"Recommended hook missing: {hook_id}")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
