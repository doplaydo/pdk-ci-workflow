# pdk-ci-workflow

Centralized CI/CD workflows, pre-commit hooks, and GitHub Actions standards for [GDSFactory](https://github.com/gdsfactory) PDK projects.

## Overview

This repository provides reusable automation tooling for Process Design Kit (PDK) repositories in the GDSFactory ecosystem. It centralizes CI/CD standards, code quality checks, and release management across multiple PDK projects, ensuring consistency and reducing maintenance overhead.

**Who should use this:** Maintainers of GDSFactory PDK repositories who want to standardize their development workflows without duplicating configuration across repos.

**Key benefits:**
- Standardized testing, linting, and type checking across all PDKs
- Automated documentation builds and deployments
- AI-powered code reviews via Claude
- 15 pre-commit hooks enforcing PDK structural compliance
- Semantic versioning and automated release notes
- Automated template sync across all managed PDK repos

## Features

This repository provides four complementary automation patterns:

- **Reusable GitHub Actions Workflows** - Complete CI/CD jobs for testing, docs, releases, and code review
- **Pre-commit Hooks** - 15 local development checks enforcing PDK organizational standards
- **Template Sync System** - Automated compliance enforcement across all managed PDK repos
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

The easiest way to onboard is to use the template files provided in `templates/`. These are automatically synced to managed PDK repos via the push-compliance workflow, but you can also copy them manually.

**1. Add reusable workflows** (copy from `templates/.github/workflows/`):
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

**2. Add pre-commit hooks** (copy from `templates/.pre-commit-config.yaml`):
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/doplaydo/pdk-ci-workflow
    rev: v1  # Use specific version tag
    hooks:
      - id: requires-pytz
      - id: check-required-files
      - id: check-pyproject-sections
      - id: check-package-init
      - id: check-cells-structure
      - id: check-tech-structure
      - id: check-pdk-object
      - id: check-test-structure
      - id: check-makefile-targets
      - id: check-workflows
      - id: check-multi-band
      - id: check-no-raw-layers
      - id: check-no-main-in-cells
      - id: check-precommit-config
      - id: check-version-sync
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

Pre-commit hooks run locally before commits to enforce PDK structural standards. All hooks are repo-level checks (`always_run: true`, `pass_filenames: false`) that use errors for required items and warnings for recommended items.

See [`hooks/README.md`](hooks/README.md) for detailed documentation of each hook.

### Installation

Add to your `.pre-commit-config.yaml` (or use the template from `templates/.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/doplaydo/pdk-ci-workflow
    rev: v1  # Use specific version tag
    hooks:
      - id: requires-pytz
      - id: check-required-files
      - id: check-pyproject-sections
      # ... add hooks as needed
```

Then install:
```bash
pip install pre-commit
pre-commit install
```

### Available Hooks

#### Project Structure

| Hook ID | What it checks |
|---------|---------------|
| `check-required-files` | README.md, LICENSE, Makefile, pyproject.toml, .pre-commit-config.yaml, tests/, workflows exist |
| `check-pyproject-sections` | Deep validation of pyproject.toml: build-system, project fields, ruff, codespell, pytest, tbump, mypy, towncrier, package-data (11 sub-checks) |
| `check-package-init` | `__version__` defined as string literal, `__all__` defined in package `__init__.py` |
| `check-version-sync` | Version consistency across pyproject.toml, tbump config, `__init__.py`, and README.md |

#### Cells & Technology

| Hook ID | What it checks |
|---------|---------------|
| `check-cells-structure` | `@gf.cell` decorators on component functions, Google-style docstrings with Args, `cells/__init__.py` re-exports |
| `check-tech-structure` | `tech.py` defines LAYER, LAYER_STACK, LAYER_VIEWS, cross_sections; optional layers.yaml cross-check |
| `check-pdk-object` | `Pdk()` constructor has required kwargs (name, cells, layers, cross_sections), uses `get_cells()` |
| `check-no-raw-layers` | Flags `(int, int)` tuples in cell files that should use `LAYER.XXX` constants |
| `check-no-main-in-cells` | Flags `if __name__ == "__main__"` blocks in cell files |

#### Infrastructure

| Hook ID | What it checks |
|---------|---------------|
| `check-makefile-targets` | Required targets (install, test) and recommended targets (docs, build, test-force, update-pre) |
| `check-workflows` | `.github/workflows/` has test_code.yml with pre-commit and test jobs |
| `check-precommit-config` | `.pre-commit-config.yaml` includes required hooks (trailing-whitespace, end-of-file-fixer, ruff, ruff-format) |

#### Multi-band & Dependencies

| Hook ID | What it checks |
|---------|---------------|
| `check-multi-band` | For multi-band PDKs: consistent module sets per band, corresponding tests, shared layers |
| `requires-pytz` | Ensures `pytz` is in `[project.dependencies]`; auto-injects if missing |

## Template Sync System

This repository includes a template synchronization system that keeps all managed PDK repos up to date with the latest workflows, pre-commit config, and GitHub configuration.

### How It Works

1. **Templates** (`templates/`) contain reference configuration files with `{{VERSION}}` placeholders
2. **PDK Registry** (`pdks.yml`) lists all managed PDK repositories as `org/repo` entries
3. **Push-compliance workflow** (`.github/workflows/push-compliance.yml`) runs on every push to `main`:
   - Reads `pdks.yml` to build a dynamic matrix of PDK repos
   - For each PDK: clones the repo, copies templates (replacing `{{VERSION}}` with the latest tag), runs pre-commit hooks, and opens a PR with any changes
4. **Local script** (`scripts/push_compliance.py`) provides the same functionality for local testing

### Template Files

| Template | Purpose |
|----------|---------|
| `.pre-commit-config.yaml` | Pre-commit hook config with all 15 PDK compliance hooks |
| `.github/workflows/test_code.yml` | Thin wrapper calling reusable test workflow |
| `.github/workflows/pages.yml` | Thin wrapper calling reusable docs workflow |
| `.github/workflows/claude-pr-review.yml` | Thin wrapper for AI code review |
| `.github/workflows/release-drafter.yml` | Thin wrapper for release management |
| `.github/dependabot.yml` | Monthly pip and github-actions dependency updates |
| `.github/release-drafter.yml` | Release note template with semantic versioning categories |

### Adding a PDK to Managed Repos

Add the `org/repo` entry to `pdks.yml`:
```yaml
pdks:
  - doplaydo/pdk-ci-demo
  - gdsfactory/cspdk       # add new PDK here
```

The next push to `main` will automatically open a compliance PR on the new repo.

### Local Sync

Use `scripts/push_compliance.py` for testing or manual sync:

```bash
# Preview changes without modifying anything
python scripts/push_compliance.py --dry-run

# Sync a single PDK
python scripts/push_compliance.py --pdk doplaydo/pdk-ci-demo

# Sync with a specific version tag
python scripts/push_compliance.py --version v0.2.0

# Sync templates and run pre-commit, but don't create PRs
python scripts/push_compliance.py --no-pr
```

See [`scripts/README.md`](scripts/README.md) for full documentation.

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

These files are provided as templates in `templates/` and are automatically synced to managed PDK repos via the push-compliance workflow. For non-managed repos, copy them manually from the templates directory.

## Requirements

PDK repositories consuming these workflows need:

### Software
- **Python:** 3.12 (minimum 3.9 supported)
- **uv:** [Astral package manager](https://github.com/astral-sh/uv)
- **Makefile:** Must define `install`, `test`, and `docs` targets

### GitHub Secrets

For PDK repositories:
- `GFP_API_KEY` - For GDSFactory Platform validation (`test_code.yml`)
- `ANTHROPIC_API_KEY` - For Claude code reviews (`claude-pr-review.yml`)

For this repository (push-compliance):
- `GH_APP_ID` - GitHub App ID for cross-repo PRs
- `GH_APP_PRIVATE_KEY` - GitHub App private key for cross-repo PRs

### GitHub Pages (for documentation)
Enable GitHub Pages in your repository settings:
- Source: GitHub Actions
- Branch: Leave as default (workflow controls deployment)

## Contributing

### Adding a New Workflow

1. Create workflow file in `.github/workflows/`
2. Use `workflow_call` trigger with defined inputs/secrets
3. Add a corresponding thin wrapper template in `templates/.github/workflows/`
4. Document in this README under "Reusable Workflows"
5. Test in a PDK repository before tagging a release

### Adding a New Pre-commit Hook

1. Create Python script in `hooks/` directory
2. Add entry point to `pyproject.toml` under `[project.scripts]`
3. Register hook in `.pre-commit-hooks.yml` with unique ID
4. Add the hook to `templates/.pre-commit-config.yaml`
5. Document in `hooks/README.md`
6. Test locally: `pre-commit try-repo . <hook-id> --verbose --all-files`

### Adding a New Template

1. Create the template file in `templates/` mirroring the target path
2. Use `{{VERSION}}` placeholder where the pdk-ci-workflow version tag should appear
3. The push-compliance workflow will automatically sync it to all managed PDKs

### Onboarding a New PDK

1. Add the `org/repo` entry to `pdks.yml`
2. Ensure the GitHub App has access to the target repository
3. Run `python scripts/push_compliance.py --dry-run --pdk org/repo` to preview
4. Push to `main` to trigger automatic compliance PR

### Versioning

This repository uses semantic versioning:
- **Major (v2.0.0):** Breaking changes to workflow inputs/outputs
- **Minor (v1.1.0):** New workflows, hooks, or backward-compatible features
- **Patch (v1.0.1):** Bug fixes, documentation updates

Consuming repositories should pin to major version tags (e.g., `@v1`) to receive minor updates and patches automatically while avoiding breaking changes.

## Repository Structure

```
pdk-ci-workflow/
├── .github/
│   ├── workflows/          # Reusable workflows + push-compliance
│   ├── release-drafter.yml # Release note template config
│   └── README.md
├── hooks/                  # Pre-commit hook implementations
│   ├── _utils.py           # Shared utilities (TOML/YAML, AST, CheckResult)
│   ├── check_*.py          # Individual hook scripts (15 total)
│   └── README.md
├── templates/              # Config templates synced to PDK repos
│   ├── .pre-commit-config.yaml
│   ├── .github/
│   └── README.md
├── scripts/                # Local CLI utilities
│   ├── push_compliance.py  # Manual template sync tool
│   └── README.md
├── actions/                # Composite actions (in development)
│   └── README.md
├── .pre-commit-hooks.yml   # Hook registration for pre-commit framework
├── pdks.yml                # Registry of managed PDK repositories
└── pyproject.toml          # Package config and hook entry points
```

## Related Projects

- [GDSFactory](https://github.com/gdsfactory/gdsfactory) - Python library for integrated circuit design
- [GDSFactory Documentation](https://gdsfactory.github.io/gdsfactory/)

## License

This project is open source. Check the repository for license details.
