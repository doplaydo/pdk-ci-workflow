"""Pre-commit hook: validate GitHub Actions workflow structure."""

from __future__ import annotations

import sys
from pathlib import Path

from hooks._utils import CheckResult, load_yaml


def _flatten_steps(job: dict) -> str:
    """Concatenate all step run/uses commands into a single searchable string."""
    parts: list[str] = []
    for step in job.get("steps", []):
        if "run" in step:
            parts.append(str(step["run"]))
        if "uses" in step:
            parts.append(str(step["uses"]))
    return " ".join(parts)


def main() -> int:
    result = CheckResult("check-workflows")

    wf_dir = Path(".github/workflows")
    if not wf_dir.is_dir():
        result.error(".github/workflows/ directory missing")
        return result.report()

    # 9a. test_code.yml (or test.yml) must exist with pre-commit job
    test_wf_path = None
    for candidate in ["test_code.yml", "test.yml"]:
        p = wf_dir / candidate
        if p.exists():
            test_wf_path = p
            break

    if test_wf_path is None:
        result.error(
            "Required workflow missing: .github/workflows/test_code.yml (or test.yml)"
        )
    else:
        data = load_yaml(str(test_wf_path))
        if data is None:
            result.error(f"{test_wf_path} could not be parsed")
        else:
            jobs = data.get("jobs", {})

            # Check if any job delegates to the centralized test_code workflow.
            # A thin wrapper job has a top-level `uses:` key instead of `steps:`.
            uses_centralized = False
            for _job_name, job_def in jobs.items():
                if not isinstance(job_def, dict):
                    continue
                uses = job_def.get("uses", "")
                if "pdk-ci-workflow" in uses and "test_code" in uses:
                    uses_centralized = True
                    break

            if not uses_centralized:
                # Check for pre-commit job
                has_precommit_job = False
                for job_name, job_def in jobs.items():
                    if not isinstance(job_def, dict):
                        continue
                    if "pre-commit" in job_name.lower():
                        has_precommit_job = True
                        break
                    steps_text = _flatten_steps(job_def)
                    if "pre-commit" in steps_text:
                        has_precommit_job = True
                        break

                if not has_precommit_job:
                    result.error(f"{test_wf_path}: no pre-commit job found")

                # 9b. Check for test_code job
                has_test_job = False
                for job_name, job_def in jobs.items():
                    if not isinstance(job_def, dict):
                        continue
                    if "test" in job_name.lower() and "pre" not in job_name.lower():
                        has_test_job = True
                        break

                if not has_test_job:
                    result.warn(f"{test_wf_path}: no test_code job found")

    # 9c. release.yml should exist
    release_path = wf_dir / "release.yml"
    if not release_path.exists():
        result.warn("Recommended workflow missing: .github/workflows/release.yml")

    return result.report()


if __name__ == "__main__":
    sys.exit(main())
