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
- Template files for onboarding new PDK repos

## Features

This repository provides four complementary automation patterns:

- **Reusable GitHub Actions Workflows** - Complete CI/CD jobs for testing, docs, releases, and code review
- **Pre-commit Hooks** - 15 PDK compliance checks plus 10 third-party tool wrappers (ruff, codespell, etc.) with centrally controlled versions
- **Templates** - Reference configuration files for onboarding new PDK repos
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

### 1. Copy workflow templates

Copy all files from `templates/.github/workflows/` into your repo. Each is a one-liner that delegates to this repo:

```yaml
# .github/workflows/test_code.yml
name: Test code
on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@main
    secrets: inherit
```

### 2. Set up pre-commit

Add to your `Makefile`:
```makefile
dev: install
	curl -sf https://raw.githubusercontent.com/doplaydo/pdk-ci-workflow/main/templates/.pre-commit-config.yaml -o .pre-commit-config.yaml
	uv run pre-commit install
```

Add to your `.gitignore`:
```
.pre-commit-config.yaml
```

Then run `make dev`.

### How pre-commit works

- **The config is never committed to PDK repos.** It lives in this repo at `templates/.pre-commit-config.yaml` and is always fetched from upstream.
- **In CI:** The `test_code.yml` reusable workflow fetches the canonical config automatically before running `pre-commit run --all-files`. No setup needed in the PDK repo.
- **Locally:** `make dev` downloads the config and installs the git hooks. Pre-commit then runs automatically on every `git commit`.
- **Versions of all tools** (ruff, codespell, nbstripout, pretty-format-toml, etc.) are controlled centrally in this repo via `additional_dependencies`. Bumping a version here propagates to all PDK repos — no downstream PRs needed.
- **PDK-specific overrides** (e.g. custom `check-yaml` excludes): keep a committed `.pre-commit-config.yaml` instead, still referencing pdk-ci-workflow as the only repo.

## Reusable Workflows

PDK repos reference these workflows via `workflow_call`. Create thin wrapper workflows in your repo's `.github/workflows/` directory.

### Available Workflows

| Workflow | Jobs | Description |
|----------|------|-------------|
| `test_code.yml` | pre-commit, test_code, test_gfp | Pre-commit (canonical config), pytest, GFP validation |
| `pages.yml` | build-docs, deploy-docs | Sphinx docs build and GitHub Pages deployment |
| `claude-pr-review.yml` | review | AI code review via Claude Sonnet 4. Runs once on PR open/reopen; re-run on demand by commenting `/claude-api review` |
| `release-drafter.yml` | update_release_draft | Auto-drafted release notes with Claude-curated changelog |
| `drc.yml` | drc | Design Rule Check with GFP and badge generation |
| `issue.yml` | add-label | Auto-labels issues with "pdk" tag |
| `test_coverage.yml` | coverage | Pytest with line coverage reporting |
| `model_coverage.yml` | model-coverage | PDK model-to-cell coverage check |
| `model_regression.yml` | model-regression | Model-specific regression tests |
| `update_badges.yml` | badges | Generate coverage, model, issue, and PR badges |

All workflows are called from PDK repos using `secrets: inherit`:

```yaml
jobs:
  test:
    uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@main
    secrets: inherit
```

See `templates/.github/workflows/` for ready-to-copy wrappers for each workflow.

### Required Secrets

PDK repos should have these secrets configured (passed automatically via `secrets: inherit`):

| Secret | Used by |
|--------|---------|
| `GFP_API_KEY` | test_code, pages, drc, test_coverage, model_coverage, model_regression, update_badges |
| `ANTHROPIC_API_KEY` | claude-pr-review, release-drafter (changelog curation) |
| `SIMCLOUD_APIKEY` | pages |
| `GITHUB_TOKEN` | release-drafter, issue, update_badges (automatic) |

## Pre-commit Hooks

Two types of hooks are defined in `.pre-commit-hooks.yaml`:

- **15 PDK compliance hooks** (`hooks/*.py`) — validate repo structure, cells, tech, tests, etc.
- **10 third-party wrapper hooks** — ruff, codespell, nbstripout, trailing-whitespace, etc. with versions pinned via `additional_dependencies` so they're controlled centrally

All hooks use `always_run: true` and `pass_filenames: false` (repo-level checks). Errors = failure, warnings = pass but alert.

See [`hooks/README.md`](hooks/README.md) for detailed documentation.

### Available Hooks

#### Project Structure

| Hook ID | What it checks |
|---------|---------------|
| `check-required-files` | README.md, CHANGELOG.md, LICENSE, Makefile, pyproject.toml, .gitignore, .pre-commit-config.yaml, tests/, test workflow, release-drafter workflow |
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
| `check-test-structure` | `tests/` directory with test files, GDS reference dirs, `difftest()` calls, `data_regression` usage |
| `check-makefile-targets` | Required targets (install, test) and recommended targets (docs, build, test-force, update-pre, dev) |
| `check-workflows` | `.github/workflows/` has test_code.yml with pre-commit and test jobs |
| `check-precommit-config` | `.pre-commit-config.yaml` includes required hooks (trailing-whitespace, end-of-file-fixer, ruff or ruff-lint, ruff-format) |
| `check-template-drift` | `.github/dependabot.yml`, `.github/release-drafter.yml`, and `.github/workflows/*.yml` thin callers match upstream templates. Auto-fixes drift. |

#### Multi-band

| Hook ID | What it checks |
|---------|---------------|
| `check-multi-band` | For multi-band PDKs: consistent module sets per band, corresponding tests, shared layers |

## Templates

Reference configuration files are provided in `templates/` for onboarding new PDK repos. Copy these files into your repo as-is — they use `@main` and `secrets: inherit`, no modification needed.

### Template Files

| Template | Purpose |
|----------|---------|
| `.pre-commit-config.yaml` | Canonical pre-commit config (PDK hooks + third-party tools with centralized versions) |
| `.github/workflows/test_code.yml` | Pre-commit, pytest, and GFP validation |
| `.github/workflows/pages.yml` | Sphinx docs build and GitHub Pages deployment |
| `.github/workflows/claude-pr-review.yml` | AI code review via Claude — runs once on PR open/reopen; re-run on demand with `/claude-api review` comment |
| `.github/workflows/release-drafter.yml` | Semantic versioning and Claude-curated release notes |
| `.github/workflows/drc.yml` | Design Rule Check via GFP |
| `.github/workflows/issue.yml` | Auto-label PDK issues |
| `.github/workflows/test_coverage.yml` | Pytest with line coverage reporting |
| `.github/workflows/model_coverage.yml` | PDK model-to-cell coverage check |
| `.github/workflows/model_regression.yml` | Model-specific regression tests |
| `.github/workflows/update_badges.yml` | Generate coverage, model, issue, and PR badges |
| `.github/dependabot.yml` | Monthly pip and github-actions dependency updates |
| `.github/release-drafter.yml` | Release note template with semantic versioning categories |

## Composite Actions

**Status:** In development

Composite actions provide reusable step sequences that can be embedded within jobs. Unlike reusable workflows, they execute on the calling job's runner and give the caller full control over the job context.

**Planned actions:**
- `setup_environment` - Set up Python, uv, and install dependencies

**Location:** `actions/*/action.yml`

Check back for updates as composite actions are added to this repository.

## Configuration Files

Some configuration files **cannot** be referenced remotely and must live directly in each PDK repository:

- `.github/dependabot.yml` - Dependency update configuration (template provided)
- `.github/release-drafter.yml` - Release note templates (template provided)
- `.github/CODEOWNERS` - Code ownership rules (no template — repo-specific)
- `Makefile` - Build targets: `install`, `test`, `docs`, `dev` (no template — repo-specific)

## Requirements

PDK repositories consuming these workflows need:

### Software
- **Python:** 3.12 (minimum 3.9 supported)
- **uv:** [Astral package manager](https://github.com/astral-sh/uv)
- **Makefile:** Must define `install`, `test`, and `docs` targets

### GitHub Secrets

For PDK repositories (passed automatically via `secrets: inherit`):
- `GFP_API_KEY` - GDSFactory Platform validation (test_code, pages, drc, test_coverage, model_coverage, model_regression, update_badges)
- `ANTHROPIC_API_KEY` - Claude code reviews and release note curation (claude-pr-review, release-drafter)
- `SIMCLOUD_APIKEY` - Simulation cloud access (pages)

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
3. Register hook in `.pre-commit-hooks.yaml` with unique ID
4. Add the hook to `templates/.pre-commit-config.yaml`
5. Document in `hooks/README.md`
6. Test locally: `pre-commit try-repo . <hook-id> --verbose --all-files`

### Adding a New Template

1. Create the template file in `templates/` mirroring the target path
2. Use `@main` to reference pdk-ci-workflow and `secrets: inherit` to pass secrets

### Versioning

This repository uses semantic versioning:
- **Major (v2.0.0):** Breaking changes to workflow inputs/outputs
- **Minor (v1.1.0):** New workflows, hooks, or backward-compatible features
- **Patch (v1.0.1):** Bug fixes, documentation updates

PDK repositories currently reference `@main` for all workflows and pre-commit hooks.

## Repository Structure

```
pdk-ci-workflow/
├── .github/
│   ├── workflows/          # Reusable workflows
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
│   └── README.md
├── actions/                # Composite actions (in development)
│   └── README.md
├── .pre-commit-hooks.yaml  # Hook registration for pre-commit framework
└── pyproject.toml          # Package config and hook entry points
```

## Related Projects

- [GDSFactory](https://github.com/gdsfactory/gdsfactory) - Python library for integrated circuit design
- [GDSFactory Documentation](https://gdsfactory.github.io/gdsfactory/)

## License

This project is open source. Check the repository for license details.
