"""Pre-commit hook: validate .pre-commit-config.yaml has required hooks."""

from __future__ import annotations

import sys

from hooks._utils import CheckResult, load_yaml

# repo substring -> required hook IDs
REQUIRED_HOOKS: dict[str, list[str]] = {
    "pre-commit/pre-commit-hooks": ["end-of-file-fixer", "trailing-whitespace"],
    "astral-sh/ruff-pre-commit": ["ruff", "ruff-format"],
}

# repo substring -> recommended hook IDs
RECOMMENDED_HOOKS: dict[str, list[str]] = {
    "kynan/nbstripout": ["nbstripout"],
    "codespell-project/codespell": ["codespell"],
}


def _match_repo(url: str, pattern: str) -> bool:
    """Check if a repo URL contains the pattern (flexible matching)."""
    return pattern in url


def main() -> int:
    result = CheckResult("check-precommit-config")

    data = load_yaml(".pre-commit-config.yaml")
    if data is None:
        result.error(".pre-commit-config.yaml missing or could not be parsed")
        return result.report()

    repos = data.get("repos", [])

    # Build map: repo_url -> set of hook ids
    repo_hooks: dict[str, set[str]] = {}
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        url = repo.get("repo", "")
        hooks = {h.get("id", "") for h in repo.get("hooks", []) if isinstance(h, dict)}
        repo_hooks[url] = hooks

    # Check required hooks
    for repo_pattern, required_ids in REQUIRED_HOOKS.items():
        matching_url = None
        for url in repo_hooks:
            if _match_repo(url, repo_pattern):
                matching_url = url
                break

        if matching_url is None:
            result.error(f"Missing repo: {repo_pattern}")
            continue

        for hook_id in required_ids:
            if hook_id not in repo_hooks[matching_url]:
                result.error(f"Missing hook '{hook_id}' from {repo_pattern}")

    # Check recommended hooks
    for repo_pattern, rec_ids in RECOMMENDED_HOOKS.items():
        matching_url = None
        for url in repo_hooks:
            if _match_repo(url, repo_pattern):
                matching_url = url
                break

        if matching_url is None:
            result.warn(f"Recommended repo missing: {repo_pattern}")
            continue

        for hook_id in rec_ids:
            if hook_id not in repo_hooks[matching_url]:
                result.warn(f"Recommended hook '{hook_id}' missing from {repo_pattern}")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
