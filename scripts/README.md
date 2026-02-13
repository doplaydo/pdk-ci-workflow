# scripts/

Local CLI utilities for managing the PDK ecosystem.

## push_compliance.py

Syncs compliance templates from `templates/` to PDK repositories listed in `pdks.yml`. This is the local equivalent of the `push-compliance.yml` GitHub Actions workflow.

### Prerequisites

- Python 3.9+
- [pyyaml](https://pypi.org/project/PyYAML/) (`pip install pyyaml`)
- [git](https://git-scm.com/) (for cloning PDK repos)
- [gh](https://cli.github.com/) (GitHub CLI, required for creating PRs)

### Usage

```bash
# Preview changes without modifying anything
python scripts/push_compliance.py --dry-run

# Sync all PDKs in pdks.yml
python scripts/push_compliance.py

# Sync a single PDK
python scripts/push_compliance.py --pdk doplaydo/pdk-ci-demo

# Override the version tag (default: latest git tag)
python scripts/push_compliance.py --version v0.2.0

# Sync templates and run pre-commit, but don't create PRs
python scripts/push_compliance.py --no-pr
```

### Flags

| Flag | Description |
|------|-------------|
| `--pdk ORG/REPO` | Sync a single PDK (substring match against `pdks.yml` entries) |
| `--dry-run` | Show what would change without cloning or modifying anything |
| `--no-pr` | Clone, sync templates, run pre-commit, but skip PR creation |
| `--version TAG` | Override the version tag used for `{{VERSION}}` replacement (default: latest git tag from this repo) |

### What It Does

For each PDK in the registry:

1. **Clone** the PDK repo into a temp directory
2. **Sync templates** from `templates/`, replacing `{{VERSION}}` with the version tag
3. **Run pre-commit** hooks (best-effort, doesn't fail on errors)
4. **Create/update PR** on the `pdk-ci-workflow/compliance-sync` branch

The script is idempotent — if templates already match, no changes are made and no PR is created.
