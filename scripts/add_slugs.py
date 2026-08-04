from pathlib import Path
from slugify import slugify

ROOT = Path("content/news")
MAX_SLUG_LENGTH = 60

count = 0
fallback = 1

for file in sorted(ROOT.rglob("index.md")):
    print(f"Checking: {file}")

    lines = file.read_text(encoding="utf-8").splitlines()

    # Skip if slug already exists
    if any(line.strip().startswith("slug =") or line.strip().startswith("slug=") for line in lines):
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

    if title:
        slug = slugify(
            title,
            lowercase=True,
            separator="-",
            max_length=MAX_SLUG_LENGTH,
            word_boundary=True,
        )
    else:
        rel = file.relative_to(ROOT)
        year = rel.parts[0] if len(rel.parts) > 1 else "0000"
        month = rel.parts[1] if len(rel.parts) > 2 else "00"
        slug = f"post-{year}{month}-{fallback:04d}"
        fallback += 1

    # Insert TOML format key-value pair
    lines.insert(title_index + 1, f'slug = "{slug}"')
    file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"  -> added slug: {slug}")
    count += 1

print(f"\nDone. Added {count} new slugs.")