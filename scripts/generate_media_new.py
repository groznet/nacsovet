#!/usr/bin/env python3
"""
Собирает media.json для каждого поста Hugo.

Раскладка поста:
    post-1/
      index.md
      X8fK2pLm.jpg        обложка — любая картинка в корне поста
      images/             галерея (необязательно)
        a9QwT7nR.webp
      videos/             видео (необязательно)
        video-1.mp4
        video-01-thumb.jpg    постер к нему

Файлы физически лежат в бакете S3, локально нужны только для сканирования.
В media.json пишутся абсолютные URL, чтобы шаблону не приходилось
склеивать пути самому.

Запуск:
    python generate_media.py            записать изменения
    python generate_media.py --dry-run  только показать, что изменится
"""

import argparse
import json
import os
import re
from urllib.parse import quote

# ==========================================
# НАСТРОЙКИ САЙТА
# ==========================================
SITE_SLUG = "nacsovet"
MEDIA_SERVER_BASE = "https://files.groznet.com"
CONTENT_SECTION = "news"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, f"../content/{CONTENT_SECTION}"))

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg")
VIDEO_EXT = (".mp4", ".webm", ".mov", ".m4v", ".ogv", ".mkv", ".avi")

IMAGES_DIR = "images"
VIDEOS_DIR = "videos"

# суффиксы, которыми помечают постер к видео
THUMB_SUFFIX_RE = re.compile(
    r"[-_.]?(thumb(nail)?|poster|preview|cover)$", re.IGNORECASE)


def natural_key(s):
    """Сортировка, где file-2 идёт раньше file-10."""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", s)]


def scan(target_dir, extensions):
    """Файлы с нужными расширениями в каталоге, без рекурсии."""
    if not os.path.isdir(target_dir):
        return []
    found = [e.name for e in os.scandir(target_dir)
             if e.is_file() and e.name.lower().endswith(extensions)]
    found.sort(key=natural_key)
    return found


def url_join(base, *parts):
    """Склеивает URL, экранируя каждый сегмент."""
    tail = "/".join(quote(p, safe="") for p in parts if p)
    return f"{base}/{tail}" if tail else base


def match_key(name):
    """Ключ сопоставления видео и постера: video-01-thumb -> video-1."""
    stem = os.path.splitext(name)[0]
    stem = THUMB_SUFFIX_RE.sub("", stem)
    # убираем ведущие нули в числах, чтобы video-01 совпало с video-1
    stem = re.sub(r"\d+", lambda m: str(int(m.group())), stem)
    return stem.lower()


def pair_videos(videos, posters, base_url):
    """Сопоставляет каждому видео его постер."""
    by_key = {}
    for p in posters:
        by_key.setdefault(match_key(p), p)

    used = set()
    result = []
    for v in videos:
        poster = by_key.get(match_key(v))
        # единственное видео и единственный постер — пара даже без совпадения имён
        if poster is None and len(videos) == 1 and len(posters) == 1:
            poster = posters[0]
        if poster:
            used.add(poster)
        result.append({
            "src": url_join(base_url, VIDEOS_DIR, v),
            "poster": url_join(base_url, VIDEOS_DIR, poster) if poster else "",
            "name": v,
        })

    orphans = [p for p in posters if p not in used]
    return result, orphans


def build(post_dir):
    """Собирает данные media.json для одного поста."""
    rel = os.path.relpath(post_dir, CONTENT_DIR).replace(os.sep, "/")
    base_url = url_join(f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}",
                        *rel.split("/")) if rel != "." else \
        f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}"

    root_images = scan(post_dir, IMAGE_EXT)
    sub_images = scan(os.path.join(post_dir, IMAGES_DIR), IMAGE_EXT)
    videos = scan(os.path.join(post_dir, VIDEOS_DIR), VIDEO_EXT)
    posters = scan(os.path.join(post_dir, VIDEOS_DIR), IMAGE_EXT)

    # 1. обложка: явный featured.* в корне, иначе первая картинка корня,
    #    иначе первая из images/
    featured = ""
    for img in root_images:
        if os.path.splitext(img)[0].lower() == "featured":
            featured = url_join(base_url, img)
            root_images.remove(img)
            break
    if not featured and root_images:
        featured = url_join(base_url, root_images.pop(0))
    if not featured and sub_images:
        featured = url_join(base_url, IMAGES_DIR, sub_images.pop(0))

    # 2. галерея: остатки корня плюс всё из images/
    #    корневые идут первыми — они ближе к посту по смыслу
    gallery = [url_join(base_url, i) for i in root_images]
    gallery += [url_join(base_url, IMAGES_DIR, i) for i in sub_images]

    # 3. видео с постерами; неиспользованные постеры уходят в галерею
    video_items, orphan_posters = pair_videos(videos, posters, base_url)
    if not videos:
        # видео нет — картинки из videos/ это просто картинки
        gallery += [url_join(base_url, VIDEOS_DIR, p) for p in orphan_posters]

    if not featured and video_items:
        featured = video_items[0]["poster"]

    return {
        "base_url": base_url,
        "featured": featured,
        "images": gallery,
        "videos": video_items,
    }


def process(post_dir, dry_run):
    """Пишет media.json, если содержимое изменилось. Возвращает статус."""
    data = build(post_dir)
    rel = os.path.relpath(post_dir, CONTENT_DIR).replace(os.sep, "/")
    path = os.path.join(post_dir, "media.json")

    old = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                old = json.load(f)
        except (json.JSONDecodeError, OSError):
            old = None

    counts = f"{len(data['images'])} изобр., {len(data['videos'])} видео"
    if old == data:
        return "same", f"без изменений: {rel} ({counts})"

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return "changed", f"{'будет обновлён' if dry_run else 'обновлён'}: {rel} ({counts})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="показать изменения, ничего не записывая")
    args = ap.parse_args()

    if not os.path.isdir(CONTENT_DIR):
        raise SystemExit(f"Каталог не найден: {CONTENT_DIR}")

    print(f"Сканирую {CONTENT_DIR}")
    print(f"База медиа: {MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}\n")

    changed = same = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        dirs[:] = [d for d in dirs if d not in (IMAGES_DIR, VIDEOS_DIR)]
        if not any(f.endswith(".md") and not f.startswith("_index")
                   for f in files):
            continue
        status, msg = process(root, args.dry_run)
        if status == "changed":
            changed += 1
            print(msg)
        else:
            same += 1

    print(f"\nОбновлено: {changed}, без изменений: {same}")
    if args.dry_run and changed:
        print("Это предпросмотр. Запустите без --dry-run, чтобы записать.")


if __name__ == "__main__":
    main()
