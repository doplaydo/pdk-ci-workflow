# templates/

Reference configuration files for onboarding new PDK repositories. Copy these files into your PDK repo as-is — they reference `@main` so they always use the latest version of pdk-ci-workflow.

## Workflow Templates

All workflow templates are minimal wrappers that delegate to the reusable workflows defined in this repo. They use `secrets: inherit` to pass all available secrets automatically.

| File | Purpose |
|------|---------|
| `.github/workflows/test_code.yml` | Pre-commit, pytest, and GFP validation |
| `.github/workflows/pages.yml` | Sphinx docs build and GitHub Pages deployment |
| `.github/workflows/claude-pr-review.yml` | AI code review via Claude |
| `.github/workflows/release-drafter.yml` | Semantic versioning and release notes |
| `.github/workflows/drc.yml` | Design Rule Check via GFP |
| `.github/workflows/issue.yml` | Auto-label PDK issues |

## Other Templates

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Canonical pre-commit config — all PDK hooks + third-party tools (ruff, codespell, etc.) with centrally controlled versions |
| `.github/dependabot.yml` | Monthly pip and github-actions dependency updates |
| `.github/release-drafter.yml` | Release note template with semantic versioning categories |

## Pre-commit Config

The `.pre-commit-config.yaml` template is the canonical config for all PDK repos. In CI, it is fetched automatically by the `test_code.yml` reusable workflow. For local development, PDK repos download it via `make dev`:

```makefile
dev: install
	curl -sf https://raw.githubusercontent.com/doplaydo/pdk-ci-workflow/main/templates/.pre-commit-config.yaml -o .pre-commit-config.yaml
	uv run pre-commit install
```
