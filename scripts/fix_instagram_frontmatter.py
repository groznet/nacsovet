#!/usr/bin/env python3
"""
Normalises front matter of the imported Instagram archive (content/instagram).

For every index.md it:
  * renames  tags -> hashtags   (keeps raw Instagram hashtags out of Hugo's tags taxonomy)
  * sets     author = "Муса Дунаев" (same as VK posts)
  * changes  the date offset +00:00 -> +03:00 (the time itself is kept as is)
  * rebuilds title from the caption (word boundary, no hashtags/@mentions/links)
  * writes   slug (transliterated title; unique per year/month; fallback = instagram id)

The caption body and every other field are left untouched. Re-running is safe.

Usage (from the site root):
    python3 scripts/fix_instagram_frontmatter.py            # dry run, prints a report
    python3 scripts/fix_instagram_frontmatter.py --write    # apply
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from slugify import slugify

ROOT = Path(__file__).resolve().parent.parent / "content" / "instagram"
AUTHOR = "Муса Дунаев"
OLD_OFFSET, NEW_OFFSET = "+00:00", "+03:00"
TITLE_MAX = 80
SLUG_MAX = 60

FM_RE = re.compile(r"\A\+\+\+\n(.*?)\n\+\+\+\n?(.*)\Z", re.S)
URL_RE = re.compile(r"https?://\S+|www\.\S+")
TAG_RE = re.compile(r"[#@][\w.]+", re.U)
LETTER_RE = re.compile(r"[^\W\d_]", re.U)


def make_title(body: str, date_str: str) -> str:
    text = ""
    for line in body.splitlines():
        cleaned = URL_RE.sub(" ", line)
        cleaned = TAG_RE.sub(" ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t-–—•·*_:;,")
        if len(LETTER_RE.findall(cleaned)) >= 6:
            text = cleaned
            break
    if not text:
        if date_str:
            return f"Публикация от {date_str[8:10]}.{date_str[5:7]}.{date_str[:4]}"
        return "Публикация Instagram"

    # prefer the first sentence when it is reasonably long
    for m in re.finditer(r"[.!?…]+(?=\s|$)", text):
        if m.end() < 20 or m.end() > TITLE_MAX:
            continue
        if m.group().startswith("."):
            pm = re.search(r"(\S+)$", text[: m.start()])
            prev = pm.group(1) if pm else ""
            nxt = text[m.end():].lstrip()
            # skip abbreviations/numbers (г., ул., 12.05.) - need a real word and a capital after
            if len(prev) < 4 or prev[-1].isdigit() or (nxt and not nxt[0].isupper()):
                continue
            return text[: m.start()].strip()
        return text[: m.end()].strip()

    if len(text) <= TITLE_MAX:
        return text.rstrip(".,;:-– ")

    cut = text[:TITLE_MAX]
    cut = cut[: cut.rfind(" ")] if " " in cut else cut
    return cut.rstrip(".,;:-–—( «\"") + "…"


def clean_slug(raw: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "", raw.lower())
    return re.sub(r"-{2,}", "-", s).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply changes (default: dry run)")
    args = ap.parse_args()

    files = sorted(ROOT.rglob("index.md"))
    plans = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            print("SKIP (no front matter):", f)
            continue
        fm_lines, body = m.group(1).split("\n"), m.group(2)

        def get(key):
            for ln in fm_lines:
                mm = re.match(rf"^{key}\s*=\s*(.*)$", ln)
                if mm:
                    try:
                        return json.loads(mm.group(1))
                    except ValueError:
                        return mm.group(1)
            return ""

        date_str = get("date") or ""
        iid = get("instagram_id") or f.parent.name
        title = make_title(body, date_str)
        if title.startswith("Публикация "):  # no usable caption -> id based slug
            slug = f"instagram-{iid}"
        else:
            raw = slugify(title, lowercase=True, separator="-", max_length=SLUG_MAX, word_boundary=True)
            slug = clean_slug(raw) or f"instagram-{iid}"
        rel = f.parent.relative_to(ROOT).parts
        bucket = "/".join(rel[:2]) if len(rel) >= 3 else "/".join(rel[:-1])
        plans.append({"file": f, "fm": fm_lines, "body": body, "title": title,
                      "slug": slug, "iid": iid, "bucket": bucket})

    # slugs must be unique inside a year/month (permalink = /instagram/:year/:month/:slug/)
    groups = defaultdict(list)
    for p in plans:
        groups[(p["bucket"], p["slug"])].append(p)
    collisions = 0
    for (_, slug), items in groups.items():
        if len(items) > 1:
            for p in items[1:]:
                p["slug"] = f"{slug}-{p['iid'][-6:]}"
                collisions += 1

    changed = 0
    for p in plans:
        out = []
        for ln in p["fm"]:
            if re.match(r"^slug\s*=", ln):
                continue
            if re.match(r"^title\s*=", ln):
                out.append("title = " + json.dumps(p["title"], ensure_ascii=False))
                out.append("slug = " + json.dumps(p["slug"], ensure_ascii=False))
                continue
            if re.match(r"^author\s*=", ln):
                out.append("author = " + json.dumps(AUTHOR, ensure_ascii=False))
                continue
            if re.match(r"^tags\s*=", ln):
                out.append(re.sub(r"^tags", "hashtags", ln))
                continue
            if re.match(r"^date\s*=", ln) and ln.rstrip().endswith(OLD_OFFSET + '"'):
                ln = ln.rstrip()[: -len(OLD_OFFSET) - 1] + NEW_OFFSET + '"'
            out.append(ln)
        new_text = "+++\n" + "\n".join(out) + "\n+++\n" + p["body"]
        if new_text != p["file"].read_text(encoding="utf-8"):
            changed += 1
            if args.write:
                p["file"].write_text(new_text, encoding="utf-8")

    print(f"posts: {len(plans)}  files {'written' if args.write else 'to change'}: {changed}  slug collisions resolved: {collisions}")
    for p in plans[:: max(1, len(plans) // 12)]:
        print(f"  {p['bucket']:>10}  {p['title'][:70]!r}  ->  {p['slug']}")


if __name__ == "__main__":
    main()
