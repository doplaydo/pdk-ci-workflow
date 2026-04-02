# templates/

Reference configuration files for onboarding new PDK repositories. Copy these files into your PDK repo and replace `{{VERSION}}` placeholders with the desired pdk-ci-workflow version tag.

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

All template files use `{{VERSION}}` as a placeholder where the pdk-ci-workflow version tag should appear. Replace this with the actual tag when copying:

```yaml
# In template:
uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@{{VERSION}}

# After replacement (e.g., tag v0.2.0):
uses: doplaydo/pdk-ci-workflow/.github/workflows/test_code.yml@v0.2.0
```

The `.pre-commit-config.yaml` template also uses the placeholder for the `rev:` field:
```yaml
- repo: https://github.com/doplaydo/pdk-ci-workflow
  rev: "{{VERSION}}"
```

## Adding a New Template

1. Create the file under `templates/` mirroring its target path in the PDK repo. For example, `templates/.github/workflows/new-workflow.yml` will be copied to `.github/workflows/new-workflow.yml` in the PDK.
2. Use `{{VERSION}}` wherever the pdk-ci-workflow version tag should appear.
3. Test the replacement locally:
   ```bash
   sed 's/{{VERSION}}/v0.2.0/g' templates/.github/workflows/new-workflow.yml
   ```
