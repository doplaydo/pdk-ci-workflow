# templates/

Copy these files into your PDK repo as-is. No modification needed.

## Workflows

Minimal wrappers — each just calls the upstream reusable workflow with `secrets: inherit`.

| File | Purpose |
|------|---------|
| `.github/workflows/test_code.yml` | Pre-commit, pytest, GFP validation |
| `.github/workflows/pages.yml` | Sphinx docs build + GitHub Pages |
| `.github/workflows/claude-pr-review.yml` | AI code review via Claude |
| `.github/workflows/release-drafter.yml` | Semantic versioning + release notes |
| `.github/workflows/drc.yml` | Design Rule Check via GFP |
| `.github/workflows/issue.yml` | Auto-label PDK issues |

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
