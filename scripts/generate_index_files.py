#!/usr/bin/env python3
"""
Generates _index.md for each year and month folder in the news archive.
"""

import argparse
import re
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
CONTENT_SECTION = "news"
TIMEZONE_OFFSET = "+03:00"  # Matches the existing _index.md files

SCRIPT_DIR = Path(__file__).resolve().parent
CONTENT_DIR = (SCRIPT_DIR.parent / "content" / CONTENT_SECTION).resolve()

YEAR_RE = re.compile(r"^\d{4}$")
MONTH_RE = re.compile(r"^(0[1-9]|1[0-2])$")

MONTH_NAMES = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


def render(title: str, year: int, month: int = 1) -> str:
    """Builds the TOML front matter used by the site's archive _index.md files."""
    return (
        "+++\n"
        f'title = "{title}"\n'
        f'date = "{year:04d}-{month:02d}-01T00:00:00{TIMEZONE_OFFSET}"\n'
        "draft = false\n"
        f'type = "{CONTENT_SECTION}"\n'
        "+++\n"
    )


def subdirs(parent: Path, pattern: re.Pattern) -> list[Path]:
    """Returns sorted subdirectories whose names match the pattern (ignoring hidden entries)."""
    return sorted(
        e for e in parent.iterdir() if e.is_dir() and pattern.match(e.name)
    )


def collect() -> list[tuple[Path, str]]:
    """Returns (folder, content) pairs for every year and month folder."""
    targets = []
    for year_dir in subdirs(CONTENT_DIR, YEAR_RE):
        year = int(year_dir.name)
        targets.append((year_dir, render(str(year), year)))

        for month_dir in subdirs(year_dir, MONTH_RE):
            month = int(month_dir.name)
            title = f"{MONTH_NAMES[month]} {year}"
            targets.append((month_dir, render(title, year, month)))
    return targets


def process(folder: Path, content: str, force: bool, dry_run: bool):
    """Writes _index.md unless it already exists. Returns status and message."""
    index_path = folder / "_index.md"
    rel = index_path.relative_to(CONTENT_DIR)

    if index_path.is_file():
        if not force:
            return "skipped", f"Skipped (already exists): {rel}"
        status = "overwritten"
        action = "Would overwrite" if dry_run else "Overwrote"
    else:
        status = "created"
        action = "Would create" if dry_run else "Created"

    if not dry_run:
        index_path.write_text(content, encoding="utf-8")

    return status, f"{action}: {rel}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate _index.md for news year and month folders."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing files"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing _index.md files"
    )
    args = parser.parse_args()

    if not CONTENT_DIR.is_dir():
        raise SystemExit(f"Directory not found: {CONTENT_DIR}")

    print(f"Scanning: {CONTENT_DIR}")
    if args.dry_run:
        print("Dry run: no files will be written")
    print()

    created = skipped = overwritten = 0

    for folder, content in collect():
        status, msg = process(folder, content, args.force, args.dry_run)
        print(msg)

        if status == "created":
            created += 1
        elif status == "overwritten":
            overwritten += 1
        else:
            skipped += 1

    suffix = " (dry run, nothing written)" if args.dry_run else ""
    print(f"\nCreated: {created}, Skipped: {skipped}, Overwritten: {overwritten}{suffix}")


if __name__ == "__main__":
    main()
