# templates/

Reference configuration files that are synced to managed PDK repositories via the push-compliance system.

## How It Works

The `push-compliance.yml` workflow (triggered on every push to `main`) copies these template files into each PDK repo listed in `pdks.yml`, replacing `{{VERSION}}` placeholders with the latest git tag from this repository (e.g., `v0.2.0`). It then runs pre-commit hooks and opens a PR with any changes.

Templates can also be synced manually using `scripts/push_compliance.py`.

## Template Files

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Pre-commit hook config with all 15 PDK compliance hooks, plus standard hooks (ruff, pre-commit-hooks, pyright) |
| `.github/workflows/test_code.yml` | Thin wrapper calling the reusable test workflow (pre-commit, pytest, GFP validation) |
| `.github/workflows/pages.yml` | Thin wrapper calling the reusable docs build and GitHub Pages deployment workflow |
| `.github/workflows/claude-pr-review.yml` | Thin wrapper for AI code review, passes `ANTHROPIC_API_KEY` secret |
| `.github/workflows/release-drafter.yml` | Thin wrapper calling the reusable release drafter workflow |
| `.github/dependabot.yml` | Dependabot config for monthly pip and github-actions dependency updates |
| `.github/release-drafter.yml` | Release note template with semantic versioning categories and auto-labeler rules |

## Version Placeholder

All template files use `{{VERSION}}` as a placeholder where the pdk-ci-workflow version tag should appear. During sync, this is replaced with the actual tag:

```yaml
# In template:
uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@{{VERSION}}

# After sync (e.g., tag v0.2.0):
uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@v0.2.0
```

The `.pre-commit-config.yaml` template also uses the placeholder for the `rev:` field:
```yaml
- repo: https://github.com/doplaydo/pdk-ci-workflow
  rev: "{{VERSION}}"
```

## Adding a New Template

1. Create the file under `templates/` mirroring its target path in the PDK repo. For example, `templates/.github/workflows/new-workflow.yml` will be synced to `.github/workflows/new-workflow.yml` in each PDK.
2. Use `{{VERSION}}` wherever the pdk-ci-workflow version tag should appear.
3. Test the replacement locally:
   ```bash
   sed 's/{{VERSION}}/v0.2.0/g' templates/.github/workflows/new-workflow.yml
   ```
4. The push-compliance workflow will automatically include the new file on the next push to `main`.

## Modifying Existing Templates

Changes to any template file will be picked up automatically by the push-compliance workflow. After pushing to `main`, compliance PRs will be opened on all managed PDK repos with the updated files.
