# CLAUDE.md

## What this repo is

This is the **centralized CI/CD and pre-commit infrastructure** for all GDSFactory PDK repositories. It is not a PDK itself — it defines the standards that PDK repos follow.

## Architecture: two layers, one rule

There are two layers:

1. **Reusable workflows** (`.github/workflows/`) — the actual CI logic (test runners, DRC checks, doc builds, badge updates). These run via `workflow_call` and contain all the steps, permissions, and configuration.

2. **Templates** (`templates/`) — thin wrapper files that PDK repos keep locally. Each template is a minimal caller that delegates to a reusable workflow. Example:

   ```yaml
   jobs:
     test:
       uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@main
       secrets: inherit
   ```

**The rule: templates are thin wrappers. They must stay thin.**

PDK repos should never inline CI logic into their workflow files. If a workflow needs to change, the change goes into the reusable workflow in this repo — not into the template or the PDK repo's copy.

## How template enforcement works

Templates are enforced via the `check-template-drift` pre-commit hook, not via GitHub branch protection or workflow permissions. This is a deliberate architectural choice:

- The hook ships canonical template content as package data
- On pre-commit run, it compares each local file byte-for-byte against the canonical version
- If drift is detected, it **overwrites** the local file (ruff-style auto-fix) and exits 1
- Second run passes clean

The enforced file list lives in `hooks/check_template_drift.py` → `TEMPLATES`.

This decentralized approach avoids cross-repo permission complexity. PDK repos pull enforcement at lint time, not at deploy time.

## When working in this repo

### Modifying CI behavior

Change the **reusable workflow** in `.github/workflows/`. Do not change the template wrapper — it should remain a thin caller.

### Adding a new workflow

1. Add the reusable workflow to `.github/workflows/`
2. Add a thin wrapper template to `templates/.github/workflows/`
3. Add the template path to the `TEMPLATES` list in `hooks/check_template_drift.py`
4. Add the template file to package data in `pyproject.toml` if it's outside `.github/`

### Adding or modifying pre-commit hooks

Hooks live in `hooks/`. Each hook has a corresponding entry in `.pre-commit-hooks.yaml`. Hook entry points are registered in `pyproject.toml` under `[project.scripts]`.

### What NOT to do

- Do not add PDK-specific logic to reusable workflows. They must work for any GDSFactory PDK.
- Do not put CI logic into templates. Templates are delegators, not implementors.
- Do not rely on cross-repo permissions for enforcement. Use pre-commit hooks.
- Do not modify templates in PDK repos directly — `check-template-drift` will revert them.

## Key files

| Path | Purpose |
|------|---------|
| `.github/workflows/` | Reusable workflow implementations (the actual CI logic) |
| `templates/` | Canonical files that PDK repos must keep in sync |
| `templates/.github/workflows/` | Thin wrapper workflow templates |
| `hooks/` | Pre-commit hook implementations |
| `hooks/check_template_drift.py` | Enforces template sync; `TEMPLATES` list defines what's enforced |
| `.pre-commit-hooks.yaml` | Hook definitions consumed by pre-commit |
| `pyproject.toml` | Package config, hook entry points, package data includes |
