"""Push compliance templates to PDK repos locally.

Usage:
    python scripts/push_compliance.py                      # Sync all PDKs
    python scripts/push_compliance.py --pdk doplaydo/pdk-ci-demo  # Single PDK
    python scripts/push_compliance.py --dry-run             # Preview changes
    python scripts/push_compliance.py --version v0.2.0      # Override version
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
PDKS_FILE = ROOT / "pdks.yml"


def get_version(override: str | None = None) -> str:
    """Get the version tag from git or use the override."""
    if override:
        return override
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "main"


def load_pdks(filter_pdk: str | None = None) -> list[str]:
    """Load the PDK registry, optionally filtering to a single entry."""
    data = yaml.safe_load(PDKS_FILE.read_text())
    pdks: list[str] = data.get("pdks", [])
    if filter_pdk:
        pdks = [p for p in pdks if filter_pdk in p]
        if not pdks:
            print(f"No PDK matching '{filter_pdk}' found in pdks.yml")
            sys.exit(1)
    return pdks


def sync_templates(target_dir: Path, version: str) -> list[str]:
    """Copy templates into target_dir, replacing {{VERSION}} placeholder.

    Returns list of files that were changed.
    """
    changed: list[str] = []
    for template_file in TEMPLATES_DIR.rglob("*"):
        if template_file.is_dir():
            continue
        rel = template_file.relative_to(TEMPLATES_DIR)
        dest = target_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        content = template_file.read_text()
        content = content.replace("{{VERSION}}", version)

        # Check if file already matches
        if dest.exists() and dest.read_text() == content:
            continue

        dest.write_text(content)
        changed.append(str(rel))
    return changed


def run_precommit(target_dir: Path) -> None:
    """Run pre-commit hooks in the target directory (best-effort)."""
    try:
        subprocess.run(
            ["pre-commit", "run", "--all-files"],
            cwd=target_dir,
            check=False,
        )
    except FileNotFoundError:
        print("  pre-commit not found, skipping hook run")


def sync_pdk(
    pdk: str,
    version: str,
    *,
    dry_run: bool = False,
    no_pr: bool = False,
) -> None:
    """Clone a PDK, sync templates, optionally run pre-commit, and create a PR."""
    print(f"\n{'=' * 60}")
    print(f"Syncing: {pdk} (version={version})")
    print(f"{'=' * 60}")

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "repo"

        # Clone
        print(f"  Cloning {pdk}...")
        result = subprocess.run(
            ["git", "clone", f"https://github.com/{pdk}.git", str(target_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  ERROR: Failed to clone {pdk}: {result.stderr.strip()}")
            return

        # Sync templates
        changed = sync_templates(target_dir, version)
        if not changed:
            print("  No changes needed.")
            return

        print(f"  Changed files: {', '.join(changed)}")

        if dry_run:
            print("  [DRY RUN] Would sync the above files and create a PR.")
            return

        # Run pre-commit
        print("  Running pre-commit hooks...")
        run_precommit(target_dir)

        if no_pr:
            print("  Skipping PR creation (--no-pr).")
            return

        # Create branch, commit, push, PR
        branch = "pdk-ci-workflow/compliance-sync"
        subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "add", "-A"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )

        # Check for actual changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=target_dir,
        )
        if result.returncode == 0:
            print("  No changes after pre-commit. Skipping.")
            return

        subprocess.run(
            ["git", "commit", "-m", f"chore: sync pdk-ci-workflow templates ({version})"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", branch, "--force"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )

        # Create or update PR
        result = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--json", "number", "--jq", ".[0].number"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print(f"  PR #{result.stdout.strip()} already exists, branch updated.")
        else:
            subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", f"chore: sync pdk-ci-workflow compliance templates ({version})",
                    "--body", (
                        "## Automated Compliance Sync\n\n"
                        "This PR was automatically generated by "
                        "[pdk-ci-workflow](https://github.com/doplaydo/pdk-ci-workflow) to sync:\n\n"
                        "- GitHub Actions workflows (thin wrappers calling reusable workflows)\n"
                        "- `.pre-commit-config.yaml` with all PDK compliance hooks\n"
                        "- `dependabot.yml` configuration\n"
                        "- `release-drafter.yml` configuration\n\n"
                        "Pre-commit hooks were run automatically — any auto-fixable issues have been applied.\n\n"
                        "Please review and merge to stay in compliance with the PDK template standards."
                    ),
                    "--base", "main",
                ],
                cwd=target_dir,
                check=True,
            )
            print(f"  Created new compliance PR for {pdk}.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Push compliance templates to PDK repositories.",
    )
    parser.add_argument(
        "--pdk",
        help="Single PDK to sync (org/repo or substring match)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making any modifications",
    )
    parser.add_argument(
        "--no-pr",
        action="store_true",
        help="Sync templates and run pre-commit but don't create PRs",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Version tag override (default: latest git tag)",
    )
    args = parser.parse_args()

    version = get_version(args.version)
    pdks = load_pdks(args.pdk)

    print(f"Version: {version}")
    print(f"PDKs to sync: {len(pdks)}")

    for pdk in pdks:
        sync_pdk(pdk, version, dry_run=args.dry_run, no_pr=args.no_pr)

    print(f"\nDone. Processed {len(pdks)} PDK(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
