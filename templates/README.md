# templates/

Copy these files into your PDK repo as-is. No modification needed.

## Workflows

Minimal wrappers — each just calls the upstream reusable workflow with `secrets: inherit`.

| File | Purpose |
|------|---------|
| `.github/workflows/test_code.yml` | Pre-commit, pytest, GFP validation |
| `.github/workflows/pages.yml` | Sphinx docs build + GitHub Pages |
| `.github/workflows/claude-pr-review.yml` | AI code review via Claude — runs once on PR open/reopen; re-run on demand with `/claude-api review` comment |
| `.github/workflows/release-drafter.yml` | Semantic versioning + Claude-curated release notes |
| `.github/workflows/drc.yml` | Design Rule Check via GFP |
| `.github/workflows/issue.yml` | Auto-label PDK issues |
| `.github/workflows/test_coverage.yml` | Pytest with line coverage reporting |
| `.github/workflows/model_coverage.yml` | PDK model-to-cell coverage check |
| `.github/workflows/model_regression.yml` | Model-specific regression tests |
| `.github/workflows/update_badges.yml` | Generate coverage, model, issue, and PR badges |

## Pre-commit Config

`.pre-commit-config.yaml` is the **canonical config** for all PDK repos.

- **Do not commit this file** — add it to `.gitignore`
- **CI fetches it automatically** via the `test_code.yml` workflow
- **Locally**, `make dev` downloads it:

```makefile
dev: install
	curl -sf https://raw.githubusercontent.com/doplaydo/pdk-ci-workflow/main/templates/.pre-commit-config.yaml -o .pre-commit-config.yaml
	uv run pre-commit install
```

## Other Config

| File | Purpose |
|------|---------|
| `.github/dependabot.yml` | Monthly pip + github-actions updates |
| `.github/release-drafter.yml` | Release note categories + auto-labeler |
