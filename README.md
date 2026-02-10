# pdk-ci-workflow

Centralized CI/CD workflows, pre-commit hooks, and GitHub Actions standards for [GDSFactory](https://github.com/gdsfactory) PDK projects.

## Overview

This repository provides reusable automation tooling for Process Design Kit (PDK) repositories in the GDSFactory ecosystem. It centralizes CI/CD standards, code quality checks, and release management across multiple PDK projects, ensuring consistency and reducing maintenance overhead.

**Who should use this:** Maintainers of GDSFactory PDK repositories who want to standardize their development workflows without duplicating configuration across repos.

**Key benefits:**
- Standardized testing, linting, and type checking across all PDKs
- Automated documentation builds and deployments
- AI-powered code reviews via Claude
- Pre-commit hooks for local development compliance
- Semantic versioning and automated release notes

## Features

This repository provides three complementary automation patterns:

- **Reusable GitHub Actions Workflows** - Complete CI/CD jobs for testing, docs, releases, and code review
- **Pre-commit Hooks** - Local development checks that enforce organizational standards
- **Composite Actions** - Shared step sequences for flexible workflow composition (in development)

Additional capabilities:
- Automated release management with semantic versioning
- AI code review powered by Claude Sonnet 4
- GitHub Pages deployment for Sphinx documentation
- Dependency update automation via Dependabot

## Architecture

This repository uses three distinct GitHub Actions patterns, each suited for different use cases:

### Reusable Workflows
**Location:** `.github/workflows/*.yml`
**Pattern:** `workflow_call`
**Use when:** You want to delegate an entire job with standardized behavior

Reusable workflows are complete, self-contained workflow definitions triggered via `workflow_call`. When a PDK repo calls a reusable workflow, it delegates the entire job — the workflow controls the runner, permissions, steps, and secret handling. The calling repo just says "run this job for me" and passes inputs. This is ideal for enforcing standardized processes where teams shouldn't customize internals.

### Composite Actions
**Location:** `actions/*/action.yml`
**Pattern:** `uses: org/repo/path/to/action@ref`
**Use when:** You want to share step sequences but retain job-level control

Composite actions are bundles of steps packaged with an `action.yml` file. They execute within a job at the step level, using the calling job's runner. The calling repo retains full control over job definition (runner, permissions, surrounding steps) and drops the composite action in as a convenience. This is ideal for sharing common step sequences (like toolchain setup) while leaving teams free to structure their own jobs.

### Pre-commit Hooks
**Location:** `hooks/*.py`
**Pattern:** Referenced via `.pre-commit-config.yaml`
**Use when:** You want local validation before code is committed

Pre-commit hooks run locally on developer machines before commits are created. They validate repository compliance against organizational standards — for example, verifying required files exist, checking field formats, or enforcing naming conventions. Hooks can auto-fix issues and fail the commit for manual review.

## Quick Start

### For consuming PDK repositories:

**1. Add reusable workflows:**
```yaml
# .github/workflows/test_code.yml
jobs:
  test:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@v1
    secrets:
      GFP_API_KEY: ${{ secrets.GFP_API_KEY }}
```

**2. Add pre-commit hooks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/doplaydo/pdk-ci-workflow
    rev: v1
    hooks:
      - id: requires-pytz
```

**3. Install pre-commit:**
```bash
pip install pre-commit
pre-commit install
```

## Reusable Workflows

PDK repos reference these workflows via `workflow_call`. Create thin wrapper workflows in your repo's `.github/workflows/` directory.

### Available Workflows

| Workflow | Jobs | Description |
|----------|------|-------------|
| `test_code.yml` | pre-commit, test_code, test_gfp | Linting (ruff), type checking (pyright), pytest, GFP validation |
| `pages.yml` | build-docs, deploy-docs | Sphinx docs build and GitHub Pages deployment |
| `claude-pr-review.yml` | claude-review | AI code review via Claude on PRs and `@claude` mentions |
| `release-drafter.yml` | update_release_draft | Auto-drafted release notes with semantic versioning |

### Usage Examples

#### Testing
Runs pre-commit checks, pytest, and GFP platform validation in parallel.

```yaml
# .github/workflows/test_code.yml
name: Test code
on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@v1
    secrets:
      GFP_API_KEY: ${{ secrets.GFP_API_KEY }}
```

**Jobs:**
- `pre-commit`: Runs ruff (linting/formatting) and pyright (type checking)
- `test_code`: Runs pytest with Python 3.12 and uv package manager
- `test_gfp`: Validates against GDSFactory Platform using `uv run gfp test`

**Required secrets:** `GFP_API_KEY`

#### Documentation
Builds Sphinx documentation and deploys to GitHub Pages.

```yaml
# .github/workflows/pages.yml
name: Build docs
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  docs:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/pages.yml@v1
```

**Jobs:**
- `build-docs`: Runs `make docs` and uploads artifact
- `deploy-docs`: Deploys to GitHub Pages (main branch only)

**Required secrets:** None

#### AI Code Review
Enables Claude-powered code review on pull requests.

```yaml
# .github/workflows/claude-pr-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
  issue_comment:
    types: [created]

jobs:
  review:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/claude-pr-review.yml@v1
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Features:**
- Automatic review on PR creation and updates
- Mention `@claude` in comments to request reviews
- Uses Claude Sonnet 4 (claude-sonnet-4-20250514)
- Reads Python files, notebooks, and documentation
- Understands GDSFactory PDK context

**Required secrets:** `ANTHROPIC_API_KEY`

#### Release Drafter
Automatically generates release notes with semantic versioning.

```yaml
# .github/workflows/release-drafter.yml
name: Release Drafter
on:
  push:
    branches: [main]

jobs:
  draft:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/release-drafter.yml@v1
```

**Features:**
- Semantic versioning based on PR labels (major/minor/patch)
- Auto-categorizes changes: Breaking, New, Bug Fixes, Maintenance, Docs, Dependencies
- Auto-labels PRs based on branch patterns (feat/*, fix/*, etc.)
- Excludes PRs labeled `skip-changelog`

**Required secrets:** None (uses `GITHUB_TOKEN`)

## Pre-commit Hooks

Pre-commit hooks run locally before commits to enforce code standards. Install them in your PDK repository to catch issues early.

### Installation

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/doplaydo/pdk-ci-workflow
    rev: v1  # Use specific version tag
    hooks:
      - id: requires-pytz
```

Then install:
```bash
pip install pre-commit
pre-commit install
```

### Available Hooks

#### `requires-pytz`
Ensures `pytz` is listed in `[project.dependencies]` of `pyproject.toml`.

**Behavior:**
- Scans `pyproject.toml` for `pytz` in dependencies
- If missing, auto-injects it with proper formatting
- Fails the commit so you can review the change
- Re-commit to proceed

**Configuration:**
```yaml
- id: requires-pytz
  name: Ensure pytz in pyproject.toml
  always_run: true
```

**Example output:**
```
❌ pytz not found in [project.dependencies]!
   🔧 Auto-adding pytz to [project.dependencies]...
   ✅ Added: "pytz",
   Staged file has been modified — please review and re-commit.
```

## Composite Actions

**Status:** In development

Composite actions provide reusable step sequences that can be embedded within jobs. Unlike reusable workflows, they execute on the calling job's runner and give the caller full control over the job context.

**Planned actions:**
- `setup_environment` - Set up Python, uv, and install dependencies

**Location:** `actions/*/action.yml`

Check back for updates as composite actions are added to this repository.

## Configuration Files

Some configuration files **cannot** be referenced remotely via GitHub Actions and must live directly in each PDK repository:

- `.github/CODEOWNERS` - Code ownership rules
- `.github/dependabot.yml` - Dependency update configuration
- `.github/release-drafter.yml` - Release note templates
- `Makefile` - Build targets (`install`, `test`, `docs`)

These files are provided by the PDK template repository and should be copied when creating a new PDK. Note that GitHub templates are a one-time copy — changes to the template do not propagate to existing repos automatically.

## Requirements

PDK repositories consuming these workflows need:

### Software
- **Python:** 3.12 (minimum 3.9 supported)
- **uv:** [Astral package manager](https://github.com/astral-sh/uv)
- **Makefile:** Must define `install`, `test`, and `docs` targets

### GitHub Secrets
Depending on which workflows you use:
- `GFP_API_KEY` - For GDSFactory Platform validation (`test_code.yml`)
- `ANTHROPIC_API_KEY` - For Claude code reviews (`claude-pr-review.yml`)

### GitHub Pages (for documentation)
Enable GitHub Pages in your repository settings:
- Source: GitHub Actions
- Branch: Leave as default (workflow controls deployment)

## Contributing

### Adding a New Workflow

1. Create workflow file in `.github/workflows/`
2. Use `workflow_call` trigger with defined inputs/secrets
3. Document in this README under "Reusable Workflows"
4. Test in a PDK repository before tagging a release

### Adding a New Pre-commit Hook

1. Create Python script in `hooks/` directory
2. Add entry point to `pyproject.toml` under `[project.scripts]`
3. Register hook in `.pre-commit-hooks.yml` with unique ID
4. Document in this README under "Pre-commit Hooks"
5. Test locally: `pre-commit try-repo . <hook-id> --verbose --all-files`

### Versioning

This repository uses semantic versioning:
- **Major (v2.0.0):** Breaking changes to workflow inputs/outputs
- **Minor (v1.1.0):** New workflows, hooks, or backward-compatible features
- **Patch (v1.0.1):** Bug fixes, documentation updates

Consuming repositories should pin to major version tags (e.g., `@v1`) to receive minor updates and patches automatically while avoiding breaking changes.

## Related Projects

- [GDSFactory](https://github.com/gdsfactory/gdsfactory) - Python library for integrated circuit design
- [GDSFactory Documentation](https://gdsfactory.github.io/gdsfactory/)

## License

This project is open source. Check the repository for license details.
