# Reusable Workflows

Reusable workflows are complete, self-contained workflow definitions that live in `.github/workflows/` and are triggered via `workflow_call`. When another repo calls a reusable workflow, it's delegating an entire job — the reusable workflow controls everything: which runner it uses, what permissions it has, what steps run, and how secrets are handled. The calling repo just says "run this job for me" and optionally passes in some inputs. This is ideal when you want to enforce a standardised process across your org where individual teams shouldn't be tweaking the internals.

## Workflows

### Reusable (called by PDK repos)

| Workflow | Trigger | Jobs | Required Secrets | Description |
|----------|---------|------|-----------------|-------------|
| `test_code.yml` | `workflow_call` | pre-commit, test_code, test_gfp | `GFP_API_KEY` | Linting (ruff), type checking (pyright), pytest, GFP platform validation |
| `pages.yml` | `workflow_call` | build-docs, deploy-docs | None | Sphinx docs build via `make docs` and GitHub Pages deployment |
| `claude-pr-review.yml` | `workflow_call` | claude-review | `ANTHROPIC_API_KEY` | AI code review via Claude Sonnet 4 on PRs and `@claude` mentions |
| `release-drafter.yml` | `workflow_call` | update_release_draft | None | Auto-drafted release notes with semantic versioning based on PR labels |

PDK repos create thin wrapper workflows that call these. See the main [README](../../README.md#reusable-workflows) for usage examples, or use the templates from `templates/.github/workflows/`.

### Internal (run by this repo)

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `push-compliance.yml` | Push to `main`, `workflow_dispatch` | Syncs templates to all PDK repos in `pdks.yml`, runs pre-commit, and opens compliance PRs. Uses a GitHub App token for cross-repo access. |
