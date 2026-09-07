import os
import re
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
CONTENT_DIR = "./content"  # Path to your Hugo content directory

# Rules for Projects mapping (Canonical Name -> List of Regex Patterns)
PROJECT_PATTERNS = {
    "Хаар-Time": [
        r"\bхаар\s*[-–—]?\s*time\b",
        r"\bхаар\s*[-–—]?\s*тайм\b",
        r"\bhaar\s*[-–—]?\s*time\b",
    ],
    "Я и весь мир": [
        r"\bя\s+и\s+весь\s+мир\b",
    ],
    "Lady-Квиз": [
        r"\blady\s*[-–—]?\s*квиз[а-я]*\b",
        r"\bледи\s*[-–—]?\s*квиз[а-я]*\b",
    ],
    "Что? Где? Когда?": [
        r"\bчто\s*\?\s*где\s*\?\s*когда\s*\?\b",
        r"\bчто\s+где\s+когда\b",
        r"\bчгк\b",
    ],
}

# Rules for Locations mapping (Canonical Name -> List of Regex Patterns)
LOCATION_PATTERNS = {
    "Грозный": [
        r"\bгрозн(ый|ом|ого|ому|ым)\b",
    ],
    "Аргун": [
        r"\bаргун(а|у|ом)?\b",
    ],
    "Гудермес": [
        r"\bгудермес(а|у|ом)?\b",
    ],
    "Шали": [
        r"\bшали\b",
    ],
    "Чеченская Республика": [
        r"\bчеченск(ая|ой|ую|ой)\s+республик(а|и|е|у|ой)\b",
        r"\bчечн(я|е|ю|ей|и)\b",
        r"\bчр\b",
    ],
    "Москва": [
        r"\bмоскв(а|ы|е|у|ой)\b",
    ],
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def match_taxonomies(text: str, patterns_dict: dict) -> list:
    """Finds all canonical taxonomy names whose patterns match inside text."""
    matched = []
    text_lower = text.lower()
    for canonical_name, patterns in patterns_dict.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched.append(canonical_name)
                break
    return matched

def format_toml_array(items: list) -> str:
    """Formats a Python list into a TOML array string: ["Item 1", "Item 2"]"""
    formatted_items = [f'"{item}"' for item in items]
    return f"[{', '.join(formatted_items)}]"

def process_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split Front Matter (TOML +++) from Body Content
    parts = content.split("+++")
    if len(parts) < 3:
        # Not a valid TOML Front Matter post
        return

    front_matter = parts[1]
    body = "+++".join(parts[2:])

    # Search in both front matter (title, etc.) and body text
    full_search_text = front_matter + "\n" + body

    matched_projects = match_taxonomies(full_search_text, PROJECT_PATTERNS)
    matched_locations = match_taxonomies(full_search_text, LOCATION_PATTERNS)

    lines = front_matter.strip().split("\n")
    updated_lines = []
    
    has_projects = False
    has_locations = False

    # Update existing lines or preserve them
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("projects ="):
            has_projects = True
            updated_lines.append(f"projects = {format_toml_array(matched_projects)}")
        elif stripped.startswith("locations ="):
            has_locations = True
            updated_lines.append(f"locations = {format_toml_array(matched_locations)}")
        else:
            updated_lines.append(line)

    # Append new taxonomy keys if not present in original front matter
    if not has_projects:
        updated_lines.append(f"projects = {format_toml_array(matched_projects)}")
    if not has_locations:
        updated_lines.append(f"locations = {format_toml_array(matched_locations)}")

    # Reconstruct the Markdown file
    new_front_matter = "\n".join(updated_lines)
    new_content = f"+++\n{new_front_matter}\n+++\n{body}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[UPDATED] {file_path.relative_to(CONTENT_DIR)} -> Projects: {matched_projects} | Locations: {matched_locations}")

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    content_path = Path(CONTENT_DIR)
    if not content_path.exists():
        print(f"Directory {CONTENT_DIR} not found.")
        return

    md_files = list(content_path.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files to analyze...\n")

    for md_file in md_files:
        process_file(md_file)

    print("\nTaxonomy generation complete!")

if __name__ == "__main__":
    main()