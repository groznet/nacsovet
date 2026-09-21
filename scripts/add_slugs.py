#!/usr/bin/env python3
# Add a slug field to each news post's front matter when one is missing,
# generating it from the post title (or a fallback identifier if the title
# is empty), truncating slugs to the configured maximum length, and saving
# the updated Markdown files.

import re
from pathlib import Path
from slugify import slugify

ROOT = Path("content/news")
MAX_SLUG_LENGTH = 60
SKIP_EXISTING_SLUGS = True  # Set to False to overwrite existing slug fields

count = 0
fallback = 1


def clean_slug(raw_slug: str) -> str:
    """Enforces strict slug safety: only a-z, 0-9, and single hyphens between words."""
    if not raw_slug:
        return ""

    # Keep only alphanumeric characters and hyphens (removes dots, colons, quotes, etc.)
    cleaned = re.sub(r"[^a-z0-9-]+", "", raw_slug.lower())

    # Replace multiple consecutive hyphens with a single hyphen
    cleaned = re.sub(r"-{2,}", "-", cleaned)

    # Strip any leading or trailing hyphens strictly
    cleaned = cleaned.strip("-")

    return cleaned


for file in sorted(ROOT.rglob("index.md")):
    # Skip section/archive indexes
    if file.name == "_index.md":
        continue

    print(f"Checking: {file}")

    lines = file.read_text(encoding="utf-8").splitlines()

    # Find if slug already exists
    existing_slug_index = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("slug =") or stripped.startswith("slug="):
            existing_slug_index = i
            break

    # Skip if slug exists and configuration is set to skip
    if existing_slug_index is not None and SKIP_EXISTING_SLUGS:
        continue

    title_index = None
    title = ""

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("title =") or stripped.startswith("title="):
            title_index = i
            # Extract title value after '='
            title = stripped.split("=", 1)[1].strip()

            # Remove surrounding quotes if present
            if (title.startswith('"') and title.endswith('"')) or (
                title.startswith("'") and title.endswith("'")
            ):
                title = title[1:-1]

            # Unescape quotes
            title = title.replace('\\"', '"').replace("\\'", "'")
            break

    if title_index is None:
        print("  -> no title field")
        continue

    # Generate raw slug from title
    if title:
        raw_slug = slugify(
            title,
            lowercase=True,
            separator="-",
            max_length=MAX_SLUG_LENGTH,
            word_boundary=True,
        )
        slug = clean_slug(raw_slug)

    # Fallback if title is empty or slugify/cleaning yields an empty string
    if not title or not slug:
        rel = file.relative_to(ROOT)
        year = rel.parts[0] if len(rel.parts) > 1 else "0000"
        month = rel.parts[1] if len(rel.parts) > 2 else "00"
        slug = f"post-{year}{month}-{fallback:04d}"
        fallback += 1

    # Update existing line or insert new line
    new_slug_line = f'slug = "{slug}"'
    if existing_slug_index is not None:
        lines[existing_slug_index] = new_slug_line
    else:
        lines.insert(title_index + 1, new_slug_line)

    file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"  -> added/updated slug: {slug}")
    count += 1

print(f"\nDone. Processed {count} slugs.")