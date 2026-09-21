#!/usr/bin/env python3
"""
Generates media.json for each Hugo post directory.
"""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

# ==========================================
# CONFIGURATION
# ==========================================
SITE_SLUG = "nacsovet"
MEDIA_SERVER_BASE = "https://files.groznet.com"
CONTENT_SECTION = "news"

SKIP_EXISTING_MEDIA_JSON = True  # Set to True to skip directories with existing media.json

SCRIPT_DIR = Path(__file__).resolve().parent
CONTENT_DIR = (SCRIPT_DIR.parent / "content" / CONTENT_SECTION).resolve()

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v", ".ogv", ".mkv", ".avi"}

IMAGES_DIR = "images"
VIDEOS_DIR = "videos"

THUMB_SUFFIX_RE = re.compile(
    r"[-_.]?(thumb(nail)?|poster|preview|cover)$", re.IGNORECASE
)


def natural_key(s: str) -> list:
    """Sorts string naturally so file-2 comes before file-10."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def scan(target_dir: Path, extensions: set[str]) -> list[str]:
    """Scans directory non-recursively for matching extensions."""
    if not target_dir.is_dir():
        return []
    found = [
        e.name
        for e in target_dir.iterdir()
        if e.is_file() and e.suffix.lower() in extensions
    ]
    found.sort(key=natural_key)
    return found


def url_join(base: str, *parts: str) -> str:
    """Joins base URL and URL-encoded path segments."""
    tail = "/".join(quote(p, safe="") for p in parts if p)
    return f"{base}/{tail}" if tail else base


def match_key(name: str) -> str:
    """Extracts a normalized matching key for videos and thumbnails."""
    stem = Path(name).stem
    stem = THUMB_SUFFIX_RE.sub("", stem)
    stem = re.sub(r"\d+", lambda m: str(int(m.group())), stem)
    return stem.lower()


def pair_videos(videos: list[str], posters: list[str], base_url: str):
    """Pairs videos with corresponding poster images."""
    by_key = {match_key(p): p for p in reversed(posters)}

    used = set()
    result = []
    for v in videos:
        poster = by_key.get(match_key(v))
        if poster is None and len(videos) == 1 and len(posters) == 1:
            poster = posters[0]
        if poster:
            used.add(poster)

        result.append(
            {
                "src": url_join(base_url, VIDEOS_DIR, v),
                "poster": url_join(base_url, VIDEOS_DIR, poster) if poster else "",
                "name": v,
            }
        )

    orphans = [p for p in posters if p not in used]
    return result, orphans


def build(post_dir: Path) -> dict:
    """Builds the media.json data structure for a post."""
    try:
        rel_parts = post_dir.relative_to(CONTENT_DIR).parts
        rel_path = "/".join(rel_parts)
    except ValueError:
        rel_path = ""

    base_url = (
        url_join(f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}", rel_path)
        if rel_path
        else f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}"
    )

    root_images = scan(post_dir, IMAGE_EXT)
    sub_images = scan(post_dir / IMAGES_DIR, IMAGE_EXT)
    videos = scan(post_dir / VIDEOS_DIR, VIDEO_EXT)
    posters = scan(post_dir / VIDEOS_DIR, IMAGE_EXT)

    # 1. Select featured image
    featured = ""
    featured_match = next(
        (img for img in root_images if Path(img).stem.lower() == "featured"),
        None,
    )

    if featured_match:
        featured = url_join(base_url, featured_match)
        root_images.remove(featured_match)
    elif root_images:
        featured = url_join(base_url, root_images.pop(0))
    elif sub_images:
        featured = url_join(base_url, IMAGES_DIR, sub_images.pop(0))

    # 2. Build image gallery
    gallery = [url_join(base_url, i) for i in root_images]
    gallery += [url_join(base_url, IMAGES_DIR, i) for i in sub_images]

    # 3. Process videos & unused posters
    video_items, orphan_posters = pair_videos(videos, posters, base_url)
    if not videos:
        gallery += [url_join(base_url, VIDEOS_DIR, p) for p in orphan_posters]

    # Fallback to poster if no featured image exists
    if not featured and video_items:
        first_poster = video_items[0].get("poster")
        if first_poster:
            featured = first_poster

    return {
        "base_url": base_url,
        "featured": featured,
        "images": gallery,
        "videos": video_items,
    }


def process(post_dir: Path, dry_run: bool):
    """Writes media.json if content changed. Returns status message."""
    rel = post_dir.relative_to(CONTENT_DIR)
    json_path = post_dir / "media.json"

    if json_path.is_file() and SKIP_EXISTING_MEDIA_JSON:
        return "skipped", f"Skipped (already exists): {rel}"

    data = build(post_dir)

    old_data = None
    if json_path.is_file():
        try:
            old_data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            old_data = None

    counts = f"{len(data['images'])} imgs, {len(data['videos'])} vids"
    if old_data == data:
        return "same", f"Unchanged: {rel} ({counts})"

    if not dry_run:
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    action = "Would update" if dry_run else "Updated"
    return "changed", f"{action}: {rel} ({counts})"


def main():
    parser = argparse.ArgumentParser(description="Generate media.json for Hugo posts.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing files"
    )
    args = parser.parse_args()

    if not CONTENT_DIR.is_dir():
        raise SystemExit(f"Directory not found: {CONTENT_DIR}")

    print(f"Scanning: {CONTENT_DIR}")
    print(f"Media Base: {MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}\n")

    changed = same = skipped = 0
    processed_dirs = set()

    for path in CONTENT_DIR.rglob("*.md"):
        if path.name.startswith("_index"):
            continue

        post_dir = path.parent
        if post_dir in processed_dirs:
            continue
        processed_dirs.add(post_dir)

        status, msg = process(post_dir, args.dry_run)

        if status == "changed":
            changed += 1
            print(msg)
        elif status == "skipped":
            skipped += 1
        else:
            same += 1

    print(f"\nUpdated: {changed}, Unchanged: {same}, Skipped: {skipped}")


if __name__ == "__main__":
    main()