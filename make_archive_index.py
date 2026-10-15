#!/usr/bin/env python3
"""
Создаёт _index.md для папок года и месяца в архиве Hugo.

Ожидаемая структура:
    content/news/
      2021/
        _index.md          <- создаётся
        12/
          _index.md        <- создаётся
          пост-1/index.md

Существующие _index.md не трогаются — запускать можно сколько угодно раз.
Файлы пишутся в UTF-8 без BOM: с BOM Hugo не разбирает фронтматтер.

Запуск:
    python make_archive_index.py                 записать
    python make_archive_index.py --dry-run       только показать
    python make_archive_index.py --force         перезаписать существующие
"""

import argparse
import os
import re

CONTENT_DIR = os.path.join("content", "news")
PAGE_TYPE = "news"          # чтобы Hugo взял layouts/news/list.html
TIMEZONE = "+03:00"

MONTHS = {
    "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
    "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
    "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь",
}

YEAR_RE = re.compile(r"^(19|20)\d{2}$")
MONTH_RE = re.compile(r"^(0[1-9]|1[0-2])$")


def front_matter(title, date):
    return (
        "+++\n"
        f'title = "{title}"\n'
        f'date = "{date}"\n'
        "draft = false\n"
        f'type = "{PAGE_TYPE}"\n'
        "+++\n"
    )


def write(path, content, force, dry_run):
    """Возвращает 'created', 'overwritten' или 'skipped'."""
    exists = os.path.exists(path)
    if exists and not force:
        return "skipped"
    if not dry_run:
        # newline="\n" — чтобы не появились CRLF, encoding без BOM
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    return "overwritten" if exists else "created"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=CONTENT_DIR,
                    help=f"каталог архива (по умолчанию {CONTENT_DIR})")
    ap.add_argument("--dry-run", action="store_true",
                    help="показать, что будет создано, ничего не записывая")
    ap.add_argument("--force", action="store_true",
                    help="перезаписать уже существующие _index.md")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        raise SystemExit(f"Каталог не найден: {args.root}")

    stats = {"created": 0, "overwritten": 0, "skipped": 0}

    for year in sorted(os.listdir(args.root)):
        year_dir = os.path.join(args.root, year)
        if not os.path.isdir(year_dir) or not YEAR_RE.match(year):
            continue

        status = write(
            os.path.join(year_dir, "_index.md"),
            front_matter(year, f"{year}-01-01T00:00:00{TIMEZONE}"),
            args.force, args.dry_run)
        stats[status] += 1
        if status != "skipped":
            print(f"{status:<12} {year}/_index.md")

        for month in sorted(os.listdir(year_dir)):
            month_dir = os.path.join(year_dir, month)
            if not os.path.isdir(month_dir) or not MONTH_RE.match(month):
                continue

            status = write(
                os.path.join(month_dir, "_index.md"),
                front_matter(f"{MONTHS[month]} {year}",
                             f"{year}-{month}-01T00:00:00{TIMEZONE}"),
                args.force, args.dry_run)
            stats[status] += 1
            if status != "skipped":
                print(f"{status:<12} {year}/{month}/_index.md")

    print(f"\nСоздано: {stats['created']}, "
          f"перезаписано: {stats['overwritten']}, "
          f"пропущено: {stats['skipped']}")
    if args.dry_run and (stats["created"] or stats["overwritten"]):
        print("Это предпросмотр. Запустите без --dry-run, чтобы записать.")


if __name__ == "__main__":
    main()
