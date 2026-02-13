# .github/

GitHub-specific configuration for the pdk-ci-workflow repository.

## Contents

### `workflows/`

Contains both **reusable workflows** (called by PDK repos via `workflow_call`) and **internal workflows** (run by this repo).

See [`workflows/README.md`](workflows/README.md) for details on each workflow.

### `release-drafter.yml`

Configuration template for the [Release Drafter](https://github.com/release-drafter/release-drafter) GitHub Action. Defines:

- **Semantic versioning**: Major/minor/patch labels map to version bumps
- **Change categories**: Breaking, New, Bug Fixes, Maintenance, Documentation, Dependency Updates
- **Auto-labeler**: Labels PRs based on branch patterns (`fix-*` -> bug, `feature-*` -> enhancement, etc.) and file patterns (`*.md` -> documentation)
- **Exclusions**: PRs labeled `skip-changelog` are omitted from release notes

This file is also available as a template at `templates/.github/release-drafter.yml` for syncing to PDK repos.
