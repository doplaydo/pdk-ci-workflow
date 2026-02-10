"""Pre-commit hook to ensure pytz IS present in top-level pyproject.toml dependencies."""

import re
import sys
from pathlib import Path

PYTZ_PATTERN = re.compile(
    r"""^\s*['"]?pytz""",
    re.IGNORECASE | re.MULTILINE,
)

DEPENDENCY_SECTION = re.compile(
    r"^(\[project\.dependencies\])",
    re.MULTILINE,
)


def find_section_range(content: str, match: re.Match) -> tuple[int, int]:
    """Return (start, end) of the body of a TOML section."""
    section_start = match.end()
    next_section = re.search(r"^\[", content[section_start:], re.MULTILINE)
    section_end = section_start + next_section.start() if next_section else len(content)
    return section_start, section_end


def check_pyproject() -> int:
    pyproject = Path("pyproject.toml")

    if not pyproject.exists():
        print("⚠️  No pyproject.toml found — skipping pytz check.")
        return 0

    content = pyproject.read_text()

    match = DEPENDENCY_SECTION.search(content)
    if not match:
        print("⚠️  No [project.dependencies] section found in pyproject.toml — skipping.")
        return 0

    section_start, section_end = find_section_range(content, match)
    section_body = content[section_start:section_end]

    if PYTZ_PATTERN.search(section_body):
        return 0

    # pytz is missing — inject it
    print("❌ pytz not found in [project.dependencies]!\n")
    print("   🔧 Auto-adding pytz to [project.dependencies]...\n")

    # Find the last non-empty line in the section to insert after
    lines = section_body.rstrip("\n").split("\n")
    insert_line = '    "pytz",\n'

    # Detect quoting/indentation style from existing entries
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in ("", "]"):
            indent = line[: len(line) - len(line.lstrip())]
            if stripped.startswith('"'):
                insert_line = f'{indent}"pytz",\n'
            elif stripped.startswith("'"):
                insert_line = f"{indent}'pytz',\n"
            else:
                insert_line = f"{indent}pytz\n"
            break

    new_content = content[:section_end].rstrip("\n") + "\n" + insert_line + content[section_end:]
    pyproject.write_text(new_content)

    print(f"   ✅ Added: {insert_line.strip()}")
    print("   Staged file has been modified — please review and re-commit.\n")

    return 1


if __name__ == "__main__":
    sys.exit(check_pyproject())