# pdk-ci-workflow

Shared CI/CD workflows and GitHub configuration for [GDSFactory](https://github.com/gdsfactory) PDK projects.

## Usage

Each workflow uses `workflow_call`, so PDK repos reference them directly. Create thin wrapper workflows in your repo's `.github/workflows/`:

### Testing

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

### Documentation

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

### AI Code Review

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

### Release Drafter

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

## Workflows

| Workflow | Jobs | Description |
|----------|------|-------------|
| `test_code.yml` | pre-commit, test_code, test_gfp | Linting (ruff), type checking (pyright), pytest, GFP validation |
| `pages.yml` | build-docs, deploy-docs | Sphinx docs build and GitHub Pages deployment |
| `claude-pr-review.yml` | claude-review | AI code review via Claude on PRs and `@claude` mentions |
| `release-drafter.yml` | update_release_draft | Auto-drafted release notes with semantic versioning |

## PDK Template

The `.github/` configuration files (`CODEOWNERS`, `dependabot.yml`, `release-drafter.yml`) and the `Makefile` cannot be referenced remotely — they must live in each PDK repo. These are provided by the PDK template repository and should be copied from there when creating a new PDK.

Note that GitHub templates are a one-time copy. Changes to the template do not propagate to existing repos automatically.

## Requirements

PDK repos consuming these workflows need:

- Python 3.12
- [uv](https://github.com/astral-sh/uv) package manager
- A `Makefile` with `install`, `test`, and `docs` targets
