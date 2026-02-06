# pdk-ci-workflow

Shared CI/CD workflows and GitHub configuration for [GDSFactory](https://github.com/gdsfactory) PDK projects.

## Workflows

### Testing (`test_code.yml`)

Runs on pull requests and pushes to `main`. Three parallel jobs:

- **pre-commit** — linting and formatting via ruff, type checking via pyright
- **test_code** — installs the project with `uv` and runs `make test`
- **test_gfp** — runs `uv run gfp test` for GDSFactory Platform validation

### Documentation (`pages.yml`)

Builds Sphinx documentation and deploys to GitHub Pages. Triggers on pull requests (build only) and pushes to `main` (build + deploy). Uses Python 3.12 and `uv`.

### AI Code Review (`claude-pr-review.yml`)

Automated code review on pull requests using Claude. Activated on PR events and when `@claude` is mentioned in issue comments. Reviews Python quality, type hints, notebook documentation, and pre-commit compliance.

### Release Drafter (`release-drafter.yml`)

Automatically drafts release notes on pushes to `main`. Categorizes changes (breaking, features, bug fixes, maintenance, docs, dependencies) and resolves semantic versions based on PR labels.

## Configuration

| File | Purpose |
|------|---------|
| `CODEOWNERS` | Default reviewers for all files |
| `dependabot.yml` | Monthly dependency updates for pip and GitHub Actions |
| `release-drafter.yml` | Release note template and auto-labeling rules |

## Requirements

- Python 3.12
- [uv](https://github.com/astral-sh/uv) package manager
- Make (for `make install`, `make test`, `make docs`)
